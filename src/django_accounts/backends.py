# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from django.contrib.auth.backends import BaseBackend
from django_utils.api.exceptions import JWTException
from rest_framework.exceptions import APIException
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import UserExtensionProxy


class JWTAccessBackend(BaseBackend):
    def authenticate(self, request, *args, **kwargs):
        try:
            jwt_auth = JWTAuthentication()
            # Dodaje te sprawdzenia tutaj (wyciagam je z metody authenticate) poniewaz nie radzi sobie z zwrotka Tuple vs None
            header = jwt_auth.get_header(request)
            if header is None:
                return None

            raw_token = jwt_auth.get_raw_token(header)
            if raw_token is None:
                return None

            user, valid_token = jwt_auth.authenticate(request)

            ext_user = UserExtensionProxy.objects.get(pk=user.pk)
            is_valid = ext_user.is_customer

            if is_valid:
                return ext_user
            else:
                return None
        except APIException as e:
            raise JWTException(message=e.default_detail, status=e.default_code, code=e.status_code)
        except Exception:
            return None

    def get_user(self, user_id):
        try:
            return UserExtensionProxy.objects.get(pk=user_id)
        except UserExtensionProxy.DoesNotExist:
            return None
