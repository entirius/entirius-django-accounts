# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from allauth.account.models import EmailAddress
from django.db import transaction
from process_logger import ProcessLoggerMixin
from rest_framework_simplejwt.token_blacklist import models as blacklist_models

from django_accounts.models import Address, Customer


class CustomerService(ProcessLoggerMixin):
    def delete_customer(self, customer: Customer) -> tuple[bool, str]:
        customer_uid = str(customer.uid)
        self.logger.add_log_param_once("customer_uid", customer_uid)
        try:
            with transaction.atomic():
                tokens_to_blacklist = blacklist_models.OutstandingToken.objects.filter(
                    user=customer.user, blacklistedtoken__isnull=True
                )

                if tokens_to_blacklist.exists():
                    blacklist = [blacklist_models.BlacklistedToken(token=token) for token in tokens_to_blacklist]
                    blacklist_models.BlacklistedToken.objects.bulk_create(blacklist)

                Address.objects.filter(customer=customer).delete()
                EmailAddress.objects.filter(user=customer.user).delete()
                customer.user.delete()
                customer.delete()

            self.logger.info(f"Successfully deleted customer account: {customer_uid}")
            return True, customer_uid
        except Exception as e:
            self.logger.exception(e)
            return False, customer_uid
