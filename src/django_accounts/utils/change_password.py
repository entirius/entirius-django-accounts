# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from allauth.account import app_settings
from allauth.account.models import EmailAddress
from django.core import signing


class EmailChangePasswordHMAC:
    def __init__(self, email_address):
        self.email_address = email_address

    @property
    def key(self):
        return signing.dumps(obj=self.email_address.pk, salt=app_settings.SALT)

    @classmethod
    def from_key(cls, key):
        try:
            max_age = 60 * 60 * 24 * app_settings.EMAIL_CONFIRMATION_EXPIRE_DAYS
            pk = signing.loads(key, max_age=max_age, salt=app_settings.SALT)

            ret = EmailChangePasswordHMAC(EmailAddress.objects.get(pk=pk))
        except (signing.SignatureExpired, signing.BadSignature, EmailAddress.DoesNotExist):
            ret = None
        return ret
