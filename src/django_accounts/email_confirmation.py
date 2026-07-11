# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import base64

from django.core.signing import TimestampSigner

from . import settings


class EmailConfirmation:
    signer = TimestampSigner()
    lifetime = 0

    @classmethod
    def get_for_user(cls, user_id: int) -> str:
        signed = cls.signer.sign(str(user_id))
        encoded = base64.b64encode(signed.encode()).decode()
        return encoded

    @classmethod
    def verify(cls, key: str) -> int:
        decoded = base64.b64decode(key).decode()
        verified = cls.signer.unsign(decoded, cls.lifetime)
        result = int(verified)
        return result


class ResetPasswordEmailConfirmation(EmailConfirmation):
    signer = TimestampSigner(salt="reset_password")
    lifetime = settings.RESET_PASSWORD_EMAIL_LIFETIME
