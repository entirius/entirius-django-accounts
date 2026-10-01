# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import json
import logging

from django.views.decorators.csrf import csrf_exempt
from django_utils.api.decorators import (
    api_view,
    authenticate,
    require_authentication,
    require_http_method,
    save_ip_and_country,
)
from django_utils.api.exceptions import Forbidden
from django_utils.api.responses import Response
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
    TokenRefreshSerializer,
    TokenVerifySerializer,
)
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from django_accounts import settings
from django_accounts.utils.decorators import channel_view

logger = logging.getLogger(__name__)


def check_if_active(customer):
    if settings.IS_ACTIVE_REQUIRED:
        if not customer.is_active:
            w = "User is not active."
            logger.debug(w)
            raise Forbidden(message=w, status="user_not_active")


def check_if_verified(customer):
    if settings.IS_VERIFY_REQUIRED:
        if not customer.is_verified:
            w = "User is not verified."
            logger.debug(w)
            raise Forbidden(message=w, status="user_not_verified")


def check_channel_acl(channel, customer):
    if channel in customer.blacklist_channels.all():
        w = "User is not allowed to login to this channel."
        logger.debug(w)
        raise Forbidden(message=w, status="user_not_allowed_in_channel")


@api_view
@channel_view
@csrf_exempt
@require_http_method("POST")
@save_ip_and_country
def token_create(request, *args, **kwargs):
    data = json.loads(request.body)
    serializer_data = dict(username=data.get("email"), password=data.get("password"))
    serializer = TokenObtainPairSerializer(data=serializer_data)
    try:
        serializer.is_valid(raise_exception=True)
    except AuthenticationFailed as e:
        logger.exception(e)
        raise Forbidden(message="Incorrect username or password", status=e.get_full_details()["code"])
    except Exception as e:
        logger.exception(e)
        raise Forbidden(message="Got undefined error")

    customer = getattr(serializer.user, "customer", None)
    if customer is None:  # valid login without a Customer profile (e.g. a staff-only account)
        raise Forbidden(message="Account has no customer profile.", status="user_not_customer")
    check_channel_acl(kwargs["channel"], customer)
    check_if_active(customer)
    check_if_verified(customer)

    tokens = serializer.validated_data
    uid = customer.uid
    request.customer = customer
    res_body = dict(customer_id=uid, **tokens)
    return Response(res_body, status="CREATED", message="token created successfully")


@api_view
@channel_view
@csrf_exempt
@require_http_method("POST")
@save_ip_and_country
def token_refresh(request, *args, **kwargs):
    data = json.loads(request.body)

    serializer_data = dict(refresh=data.get("refresh"))
    serializer = TokenRefreshSerializer(data=serializer_data)
    try:
        serializer.is_valid(raise_exception=False)
    except Exception as e:
        raise Forbidden(message=str(e))
    tokens = serializer.validated_data
    token_access = JWTAuthentication().get_validated_token(tokens["access"])
    user = JWTAuthentication().get_user(token_access)
    check_channel_acl(kwargs["channel"], user.customer)
    check_if_active(user.customer)
    check_if_verified(user.customer)
    uid = user.customer.uid
    request.customer = user.customer
    res_body = dict(customer_id=uid, **tokens)
    return Response(res_body)


@csrf_exempt
@api_view
@authenticate
@require_authentication
@require_http_method("POST")
def token_blacklist(request, *args, **kwargs):
    data = json.loads(request.body)
    refresh_token = data.get("refresh")
    try:
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response(data={}, message="Refresh token blacklisted", status="BLACKLISTED")
    except TokenError as e:
        return Response(data={}, message=str(e), status="BLACKLISTED")


@api_view
@csrf_exempt
@require_http_method("POST")
def token_validate(request, *args, **kwargs):
    data = json.loads(request.body)
    try:
        # This rises exceptions if token is invalid
        token_obj = AccessToken(data.get("access"))
        serializer_data = dict(token=data.get("access"))
        serializer = TokenVerifySerializer(data=serializer_data)
        is_valid = serializer.is_valid()
        reason = serializer.errors
    except Exception as e:
        is_valid = False
        reason = {"access": str(e)}
    result = dict(is_valid=is_valid, reason=reason)
    return Response(result, status="VALIDATED", message="token validated successfully")
