# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Tests for Accounts Admin API v2 (read-only endpoints)."""

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from django_accounts.models import Customer
from django_accounts.schemas.responses.customer import CustomerDetailResponse, CustomerListItem

User = get_user_model()

CUSTOMER_LIST_URL = "accounts-admin-customer-list"
CUSTOMER_DETAIL_URL = "accounts-admin-customer-detail"
GROUP_LIST_URL = "accounts-admin-group-list"
CHANNEL_LIST_URL = "accounts-admin-channel-list"

FAKE_UID = "00000000-0000-0000-0000-000000000000"


# --- Auth Tests: Customers ---


@pytest.mark.django_db
class TestCustomerListAuth:
    def test_unauthenticated_returns_401(self, api_client):
        resp = api_client.get(reverse(CUSTOMER_LIST_URL))
        assert resp.status_code == 401

    def test_regular_user_returns_403(self, regular_client):
        resp = regular_client.get(reverse(CUSTOMER_LIST_URL))
        assert resp.status_code == 403

    def test_admin_returns_200(self, admin_client):
        resp = admin_client.get(reverse(CUSTOMER_LIST_URL))
        assert resp.status_code == 200


@pytest.mark.django_db
class TestCustomerDetailAuth:
    def test_unauthenticated_returns_401(self, api_client):
        resp = api_client.get(reverse(CUSTOMER_DETAIL_URL, kwargs={"uid": FAKE_UID}))
        assert resp.status_code == 401

    def test_regular_user_returns_403(self, regular_client):
        resp = regular_client.get(reverse(CUSTOMER_DETAIL_URL, kwargs={"uid": FAKE_UID}))
        assert resp.status_code == 403

    def test_nonexistent_uid_returns_404(self, admin_client):
        resp = admin_client.get(reverse(CUSTOMER_DETAIL_URL, kwargs={"uid": FAKE_UID}))
        assert resp.status_code == 404


# --- Auth Tests: Groups ---


@pytest.mark.django_db
class TestGroupListAuth:
    def test_unauthenticated_returns_401(self, api_client):
        resp = api_client.get(reverse(GROUP_LIST_URL))
        assert resp.status_code == 401

    def test_regular_user_returns_403(self, regular_client):
        resp = regular_client.get(reverse(GROUP_LIST_URL))
        assert resp.status_code == 403

    def test_admin_returns_200(self, admin_client):
        resp = admin_client.get(reverse(GROUP_LIST_URL))
        assert resp.status_code == 200


# --- Auth Tests: Channels ---


@pytest.mark.django_db
class TestChannelListAuth:
    def test_unauthenticated_returns_401(self, api_client):
        resp = api_client.get(reverse(CHANNEL_LIST_URL))
        assert resp.status_code == 401

    def test_regular_user_returns_403(self, regular_client):
        resp = regular_client.get(reverse(CHANNEL_LIST_URL))
        assert resp.status_code == 403

    def test_admin_returns_200(self, admin_client):
        resp = admin_client.get(reverse(CHANNEL_LIST_URL))
        assert resp.status_code == 200


# --- Customer List ---


@pytest.mark.django_db
class TestCustomerList:
    def test_pagination_structure(self, admin_client, customer):
        resp = admin_client.get(reverse(CUSTOMER_LIST_URL))
        data = resp.json()
        assert "count" in data
        assert "next" in data
        assert "previous" in data
        assert "results" in data

    def test_returns_customer_fields_and_schema_contract(self, admin_client, customer):
        resp = admin_client.get(reverse(CUSTOMER_LIST_URL))
        result = resp.json()["results"][0]
        # Validate against Pydantic schema — catches type mismatches
        validated = CustomerListItem(**result)
        assert validated.uid == str(customer.uid)
        assert validated.email == customer.user.email
        assert validated.firstname == customer.user.first_name

    def test_search_by_email(self, admin_client, customer):
        resp = admin_client.get(reverse(CUSTOMER_LIST_URL), {"search": customer.user.email[:5]})
        assert resp.json()["count"] >= 1

    def test_search_by_name(self, admin_client, customer):
        resp = admin_client.get(reverse(CUSTOMER_LIST_URL), {"search": customer.user.first_name})
        assert resp.json()["count"] >= 1

    def test_filter_by_group(self, admin_client, customer_with_details):
        resp = admin_client.get(reverse(CUSTOMER_LIST_URL), {"group": "vip"})
        assert resp.json()["count"] >= 1

    def test_filter_by_channel(self, admin_client, customer):
        resp = admin_client.get(reverse(CUSTOMER_LIST_URL), {"source_channel": "test-channel"})
        assert resp.json()["count"] >= 1

    def test_filter_by_active(self, admin_client, customer):
        resp = admin_client.get(reverse(CUSTOMER_LIST_URL), {"is_active": "true"})
        for result in resp.json()["results"]:
            assert result["is_active"] is True

    def test_filter_by_verified(self, admin_client, customer):
        resp = admin_client.get(reverse(CUSTOMER_LIST_URL), {"is_verified": "true"})
        for result in resp.json()["results"]:
            assert result["is_verified"] is True

    def test_ordering_by_email_verifies_order(self, admin_client, customer):
        # Create a second customer with a known email for ordering verification
        u2 = User.objects.create_user(username="aaa@test.com", email="aaa@test.com", password="Test1234!")
        Customer.objects.create(user=u2, is_active=True)

        resp = admin_client.get(reverse(CUSTOMER_LIST_URL), {"ordering": "email"})
        results = resp.json()["results"]
        emails = [r["email"] for r in results]
        assert emails == sorted(emails), f"Expected sorted order, got: {emails}"


# --- Customer Detail ---


@pytest.mark.django_db
class TestCustomerDetail:
    def _url(self, uid):
        return reverse(CUSTOMER_DETAIL_URL, kwargs={"uid": str(uid)})

    def test_full_response_shape_and_schema_contract(self, admin_client, customer_with_details):
        resp = admin_client.get(self._url(customer_with_details.uid))
        data = resp.json()
        # Validate against Pydantic schema — catches missing fields, type mismatches
        validated = CustomerDetailResponse(**data)
        assert validated.uid == str(customer_with_details.uid)
        assert validated.dialling_code == "+48"
        assert validated.group is not None
        assert validated.group.code == "vip"

    def test_addresses_embedded_with_defaults(self, admin_client, customer_with_addresses):
        resp = admin_client.get(self._url(customer_with_addresses.uid))
        data = resp.json()
        assert data["addresses_count"] == 2
        assert len(data["addresses"]) == 2

        billing = next(a for a in data["addresses"] if a["is_default_billing"])
        assert billing["address_id"] == customer_with_addresses.billing_address_id

        shipping = next(a for a in data["addresses"] if a["is_default_shipping"])
        assert shipping["address_id"] == customer_with_addresses.shipping_address_id

    def test_wishlist_items_count(self, admin_client, wishlist_with_products):
        resp = admin_client.get(self._url(wishlist_with_products.uid))
        assert resp.json()["wishlist_items_count"] == 2

    def test_blacklist_channels_serialized(self, admin_client, customer, second_channel):
        customer.blacklist_channels.add(second_channel)
        resp = admin_client.get(self._url(customer.uid))
        data = resp.json()
        assert len(data["blacklist_channels"]) == 1
        assert data["blacklist_channels"][0]["idx"] == "second-channel"
        assert data["blacklist_channels"][0]["label"] == "Second Channel"


# --- Groups List ---


@pytest.mark.django_db
class TestGroupList:
    def test_pagination_structure(self, admin_client, group):
        resp = admin_client.get(reverse(GROUP_LIST_URL))
        data = resp.json()
        assert "count" in data
        assert "results" in data
        assert "next" in data
        assert "previous" in data

    def test_returns_groups_with_count(self, admin_client, group, customer_with_details):
        resp = admin_client.get(reverse(GROUP_LIST_URL))
        results = resp.json()["results"]
        vip = next(g for g in results if g["code"] == "vip")
        assert vip["customers_count"] >= 1
        assert "name" in vip
        assert "is_active" in vip
        assert "created_at" in vip


# --- Channels List ---


@pytest.mark.django_db
class TestChannelList:
    def test_pagination_structure(self, admin_client, channel):
        resp = admin_client.get(reverse(CHANNEL_LIST_URL))
        data = resp.json()
        assert "count" in data
        assert "results" in data
        assert "next" in data
        assert "previous" in data

    def test_returns_channels_with_language(self, admin_client, channel):
        resp = admin_client.get(reverse(CHANNEL_LIST_URL))
        results = resp.json()["results"]
        ch = next(c for c in results if c["idx"] == "test-channel")
        assert ch["label"] == "Test Channel"
        assert ch["language"] == "en"


# --- Edge Cases ---


@pytest.mark.django_db
class TestEdgeCases:
    def test_empty_customer_list(self, admin_client):
        resp = admin_client.get(reverse(CUSTOMER_LIST_URL))
        assert resp.json()["count"] == 0
        assert resp.json()["results"] == []

    def test_customer_no_group_no_channel(self, admin_client):
        u = User.objects.create_user(username="nogroup@test.com", email="nogroup@test.com", password="Test1234!")
        c = Customer.objects.create(user=u, is_active=True)
        resp = admin_client.get(reverse(CUSTOMER_DETAIL_URL, kwargs={"uid": str(c.uid)}))
        data = resp.json()
        assert data["group"] is None
        assert data["source_channel"] is None

    def test_customer_no_addresses(self, admin_client, customer):
        resp = admin_client.get(reverse(CUSTOMER_DETAIL_URL, kwargs={"uid": str(customer.uid)}))
        data = resp.json()
        assert data["addresses"] == []
        assert data["addresses_count"] == 0

    def test_customer_no_wishlist(self, admin_client, customer):
        resp = admin_client.get(reverse(CUSTOMER_DETAIL_URL, kwargs={"uid": str(customer.uid)}))
        assert resp.json()["wishlist_items_count"] == 0
