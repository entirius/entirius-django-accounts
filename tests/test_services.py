# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model
from process_logger import ProcessLogger

from django_accounts.models import Address, Customer
from django_accounts.services.customer import CustomerService

User = get_user_model()


def _make_service() -> CustomerService:
    service = CustomerService()
    service.set_logger(ProcessLogger("test-accounts"))
    return service


class TestCustomerService:
    def test_delete_customer_success(self, customer):
        customer_uid = str(customer.uid)
        user_pk = customer.user.pk

        service = _make_service()
        success, returned_uid = service.delete_customer(customer)

        assert success is True
        assert returned_uid == customer_uid
        assert not Customer.objects.filter(uid=customer_uid).exists()
        assert not User.objects.filter(pk=user_pk).exists()

    def test_delete_customer_cascades_addresses(self, address):
        customer = address.customer
        assert Address.objects.filter(customer=customer).count() == 1

        service = _make_service()
        success, _ = service.delete_customer(customer)

        assert success is True
        assert Address.objects.filter(customer_id=customer.pk).count() == 0

    def test_delete_customer_removes_email_addresses(self, customer):
        user = customer.user
        assert EmailAddress.objects.filter(user=user).exists()

        service = _make_service()
        service.delete_customer(customer)

        assert not EmailAddress.objects.filter(user_id=user.pk).exists()

    def test_delete_customer_returns_uid_on_failure(self, db, language, channel):
        """Verify the service returns (False, uid) when deletion fails."""
        user = User.objects.create_user(
            username="fail@example.com",
            email="fail@example.com",
            password="Test1234!",
        )
        customer = Customer.objects.create(user=user, source_channel=channel)
        customer_uid = str(customer.uid)

        # Delete the user first so the service's atomic block will fail
        user.delete()

        service = _make_service()
        success, returned_uid = service.delete_customer(customer)

        assert success is False
        assert returned_uid == customer_uid
