# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from django_accounts.models import Customer
from django_accounts.services.customer import CustomerService


def admin_customer_delete(email: str, logger) -> tuple[bool, list[str] | None, list[str] | None]:
    customers = Customer.objects.filter(user__email=email)
    if not customers.exists():
        return False, None, None

    customer_service = CustomerService()
    customer_service.set_logger(logger)

    success = []
    uids_success = []
    uids_failed = []
    for customer in customers:
        is_success, uid = customer_service.delete_customer(customer)
        if is_success:
            success.append(True)
            uids_success.append(uid)
        else:
            success.append(False)
            uids_failed.append(uid)

    return all(success), uids_success, uids_failed
