# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from datetime import datetime, timedelta

import jwt
from django.utils import timezone
from jwt.exceptions import InvalidTokenError

from . import settings

key = settings.JWT_SECRET
algorithm = settings.JWT_ALGORITHM


class TokenException(InvalidTokenError):
    pass


class TokenHelper:
    @staticmethod
    def encode(data: dict) -> str:
        return jwt.encode(data, key, algorithm)

    @staticmethod
    def decode(token: str) -> dict:
        return jwt.decode(token, key, algorithms=[algorithm], options={"require": ["access", "refresh", "iat", "exp"]})


class Token:
    helper = TokenHelper
    token_type: str = None
    lifetime: int = None

    @classmethod
    def get_data(cls, access: str, refresh: str, issued_at: datetime, customer_id) -> dict:
        # https://pyjwt.readthedocs.io/en/latest/usage.html#registered-claim-names
        expires_at = issued_at + timedelta(minutes=cls.lifetime)
        data = {
            "access": access,
            "refresh": refresh,
            "customer_id": customer_id,
            "iat": issued_at.timestamp(),
            "exp": expires_at.timestamp(),
        }
        return data

    @classmethod
    def verify_data(cls, data: dict, time_now: datetime | None = None):
        if time_now is not None:
            issued_at = time_now.timestamp()
            exp = datetime.fromtimestamp(float(data["exp"]))
            is_expired = time_now > exp
        else:
            is_expired = False

        return is_expired


class TokenAccessSocialLogin(Token):
    lifetime = settings.JWT_REFRESH_LIFETIME

    @classmethod
    def get_access_token(cls, refresh: str) -> str:
        data = cls.helper.decode(refresh)
        acc_data = cls.access_token_class.get_data(
            data["uid"], datetime.fromtimestamp(data["iat"], timezone.get_current_timezone())
        )
        return cls.helper.encode(acc_data)
