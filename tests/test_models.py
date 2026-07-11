# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from django_accounts.models import (
    Address,
    APIAdminKey,
    Channel,
    Customer,
    Group,
    ProductRepresentation,
    Revoke,
    Wishlist,
    WishlistProduct,
)

User = get_user_model()


# ---------------------------------------------------------------------------
# Customer
# ---------------------------------------------------------------------------


class TestCustomer:
    def test_create_customer(self, customer):
        assert customer.is_active is True
        assert customer.is_verified is True
        assert customer.uid is not None

    def test_customer_uid_is_unique(self, customer, db):
        user2 = User.objects.create_user(
            username="other@example.com",
            email="other@example.com",
            password="Test1234!",
        )
        c2 = Customer.objects.create(user=user2)
        assert c2.uid != customer.uid

    def test_customer_first_name_delegates_to_user(self, customer):
        assert customer.first_name == "John"

    def test_customer_last_name_delegates_to_user(self, customer):
        assert customer.last_name == "Doe"

    def test_customer_email_property(self, customer):
        email = customer.email
        assert email is not None
        assert email.email == "testuser@example.com"

    def test_customer_str(self, customer):
        assert str(customer) == str(customer.user)

    def test_create_from_user_manager(self, user_with_email, channel):
        c = Customer.objects.create_from_user(
            user=user_with_email,
            phone="+48123456789",
            is_active=True,
            channel=channel,
        )
        c.save()
        assert c.phone == "+48123456789"
        assert c.source_channel == channel

    def test_customer_sex_choices(self, customer):
        customer.sex = Customer.Sex.MALE
        customer.save()
        customer.refresh_from_db()
        assert customer.sex == "male"

    def test_customer_extra_json(self, customer):
        customer.extra = {"loyalty_points": 100}
        customer.save()
        customer.refresh_from_db()
        assert customer.extra["loyalty_points"] == 100

    def test_check_blacklist_removes_source_channel(self, customer, channel, second_channel):
        customer.blacklist_channels.add(channel, second_channel)
        customer.check_blacklist()
        # source_channel should be removed from blacklist
        blacklisted = list(customer.blacklist_channels.all())
        assert channel not in blacklisted
        assert second_channel in blacklisted

    def test_cascade_delete_user_deletes_customer(self, customer):
        user = customer.user
        user.delete()
        assert not Customer.objects.filter(pk=customer.pk).exists()


# ---------------------------------------------------------------------------
# Channel
# ---------------------------------------------------------------------------


class TestChannel:
    def test_create_channel(self, channel):
        assert channel.idx == "test-channel"
        assert channel.label == "Test Channel"

    def test_channel_idx_unique(self, channel, language):
        with pytest.raises(IntegrityError):
            Channel.objects.create(
                idx="test-channel",
                label="Duplicate Channel",
                language=language,
            )

    def test_channel_label_unique(self, channel, language):
        with pytest.raises(IntegrityError):
            Channel.objects.create(
                idx="different-idx",
                label="Test Channel",
                language=language,
            )

    def test_channel_str(self, channel):
        assert str(channel) == "Test Channel [test-channel]"


# ---------------------------------------------------------------------------
# Group
# ---------------------------------------------------------------------------


class TestGroup:
    def test_create_group(self, group):
        assert group.code == "vip"
        assert group.name == "VIP Customers"
        assert group.is_active is True

    def test_group_code_unique(self, group):
        with pytest.raises(IntegrityError):
            Group.objects.create(code="vip", name="Other Group")

    def test_group_name_unique(self, group):
        with pytest.raises(IntegrityError):
            Group.objects.create(code="other", name="VIP Customers")

    def test_group_str(self, group):
        assert str(group) == "VIP Customers"

    def test_customer_group_assignment(self, customer, group):
        customer.group = group
        customer.save()
        customer.refresh_from_db()
        assert customer.group == group


# ---------------------------------------------------------------------------
# Address
# ---------------------------------------------------------------------------


class TestAddress:
    def test_create_address(self, address):
        assert address.pk is not None
        assert address.is_company is False

    def test_address_as_dict(self, address):
        d = address.as_dict
        assert d["firstname"] == "John"
        assert d["city"] == "Warsaw"
        assert d["address_id"] == str(address.pk)

    def test_address_auto_sets_is_company_when_none(self, customer):
        """When is_company is None, save() auto-detects from tax_id."""
        addr = Address(
            customer=customer,
            company="ACME Corp",
            tax_id="1234567890",
            street="Business St 1",
            city="Gdansk",
            postcode="80-001",
            telephone="987654321",
            dialling_code="+48",
            country_code="PL",
            is_company=None,
        )
        addr.save()
        assert addr.is_company is True

    def test_address_auto_sets_not_company_when_no_tax_id(self, customer):
        addr = Address(
            customer=customer,
            firstname="John",
            lastname="Doe",
            street="St 1",
            city="City",
            postcode="00-000",
            telephone="123",
            dialling_code="+48",
            country_code="PL",
            is_company=None,
        )
        addr.save()
        assert addr.is_company is False

    def test_address_clean_validates_name_or_company(self, customer):
        addr = Address(
            customer=customer,
            firstname=None,
            lastname=None,
            company=None,
            street="No Name St",
            city="Nowhere",
            postcode="00-000",
            telephone="111",
            dialling_code="+48",
            country_code="PL",
        )
        with pytest.raises(ValidationError):
            addr.clean()

    def test_address_clean_validates_company_data(self, customer):
        addr = Address(
            customer=customer,
            firstname="John",
            lastname="Doe",
            is_company=True,
            company=None,
            tax_id=None,
            street="St 1",
            city="City",
            postcode="00-000",
            telephone="111",
            dialling_code="+48",
            country_code="PL",
        )
        with pytest.raises(ValidationError):
            addr.clean()

    def test_address_update_from_dict(self, address):
        address.update_from_dict({"street": "New St", "city": "NewCity"}, address.customer)
        address.refresh_from_db()
        assert address.street == "New St"
        assert address.city == "NewCity"

    def test_address_update_from_dict_raises_if_not_saved(self, customer):
        addr = Address(customer=customer)
        with pytest.raises(Exception, match="Cannot update"):
            addr.update_from_dict({"street": "X"}, customer)

    def test_address_cascade_delete_with_customer(self, address):
        customer_pk = address.customer.pk
        address.customer.user.delete()
        assert not Address.objects.filter(customer_id=customer_pk).exists()

    def test_address_str_with_name(self, address):
        assert "John" in str(address)
        assert "Warsaw" in str(address)

    def test_address_str_with_company(self, customer):
        addr = Address.objects.create(
            customer=customer,
            company="ACME",
            tax_id="123",
            street="Biz St",
            city="Gdansk",
            postcode="80-001",
            telephone="123",
            dialling_code="+48",
            country_code="PL",
        )
        assert "ACME" in str(addr)

    def test_default_shipping_billing_address(self, address):
        customer = address.customer
        customer.shipping_address = address
        customer.billing_address = address
        customer.save()
        customer.refresh_from_db()
        assert customer.shipping_address == address
        assert customer.billing_address == address

    def test_make_address_as_default_for_customer(self, address):
        customer = address.customer
        Address.objects.make_address_as_default_for_customer(address, customer, "shipping")
        customer.refresh_from_db()
        assert customer.shipping_address == address


# ---------------------------------------------------------------------------
# ProductRepresentation
# ---------------------------------------------------------------------------


class TestProductRepresentation:
    def test_create_product_representation(self, channel):
        pr = ProductRepresentation.objects.create(
            sku="CHAIR-001",
            name_t9n={"en": "Office Chair", "pl": "Krzeslo biurowe"},
            channel=channel,
        )
        assert pr.sku == "CHAIR-001"
        assert pr.name == "Office Chair"

    def test_name_lang_fallback_to_sku(self, channel):
        pr = ProductRepresentation.objects.create(
            sku="NO-NAME-001",
            name_t9n=None,
            channel=channel,
        )
        assert pr.name == "NO-NAME-001"

    def test_name_lang_fallback_to_default_lang(self, channel):
        pr = ProductRepresentation.objects.create(
            sku="ITEM-001",
            name_t9n={"en": "Item One"},
            channel=channel,
        )
        # Requesting a language that doesn't exist falls back to T9N_DEFAULT_LANG ("en" in tests)
        assert pr.name_lang("de") == "Item One"

    def test_unique_sku_per_channel(self, channel):
        ProductRepresentation.objects.create(sku="DUP-001", channel=channel)
        with pytest.raises(IntegrityError):
            ProductRepresentation.objects.create(sku="DUP-001", channel=channel)

    def test_same_sku_different_channels(self, channel, second_channel):
        pr1 = ProductRepresentation.objects.create(sku="SHARED-001", channel=channel)
        pr2 = ProductRepresentation.objects.create(sku="SHARED-001", channel=second_channel)
        assert pr1.pk != pr2.pk


# ---------------------------------------------------------------------------
# Wishlist
# ---------------------------------------------------------------------------


class TestWishlist:
    def test_create_wishlist(self, customer, channel):
        wl = Wishlist.objects.create(customer=customer, channel=channel)
        assert wl.uid is not None
        assert wl.customer == customer

    def test_unique_wishlist_per_customer_channel(self, customer, channel):
        Wishlist.objects.create(customer=customer, channel=channel)
        with pytest.raises(IntegrityError):
            Wishlist.objects.create(customer=customer, channel=channel)

    def test_wishlist_different_channels(self, customer, channel, second_channel):
        wl1 = Wishlist.objects.create(customer=customer, channel=channel)
        wl2 = Wishlist.objects.create(customer=customer, channel=second_channel)
        assert wl1.pk != wl2.pk

    def test_add_customer_to_guest_wishlist(self, customer, channel):
        wl = Wishlist.objects.create(customer=None, channel=channel)
        wl.add_customer(customer)
        wl.refresh_from_db()
        assert wl.customer == customer


# ---------------------------------------------------------------------------
# WishlistProduct
# ---------------------------------------------------------------------------


class TestWishlistProduct:
    def test_add_extra(self, customer, channel):
        wl = Wishlist.objects.create(customer=customer, channel=channel)
        pr = ProductRepresentation.objects.create(sku="WP-001", channel=channel)
        wp = WishlistProduct.objects.create(wishlist=wl, product=pr)
        wp.add_extra("color", "red")
        wp.refresh_from_db()
        assert wp.extra["color"] == "red"

    def test_remove_extra(self, customer, channel):
        wl = Wishlist.objects.create(customer=customer, channel=channel)
        pr = ProductRepresentation.objects.create(sku="WP-002", channel=channel)
        wp = WishlistProduct.objects.create(wishlist=wl, product=pr, extra={"size": "L"})
        wp.remove_extra("size")
        wp.refresh_from_db()
        assert "size" not in (wp.extra or {})

    def test_add_source(self, customer, channel):
        wl = Wishlist.objects.create(customer=customer, channel=channel)
        pr = ProductRepresentation.objects.create(sku="WP-003", channel=channel)
        wp = WishlistProduct.objects.create(wishlist=wl, product=pr)
        wp.add_source("pwa")
        wp.refresh_from_db()
        assert "pwa" in wp.sources

    def test_add_source_deduplicates(self, customer, channel):
        wl = Wishlist.objects.create(customer=customer, channel=channel)
        pr = ProductRepresentation.objects.create(sku="WP-004", channel=channel)
        wp = WishlistProduct.objects.create(wishlist=wl, product=pr)
        wp.add_source("pwa")
        wp.add_source("pwa")
        wp.refresh_from_db()
        assert wp.sources.count("pwa") == 1


# ---------------------------------------------------------------------------
# APIAdminKey
# ---------------------------------------------------------------------------


class TestAPIAdminKey:
    def test_auto_generates_key_on_save(self, channel):
        key = APIAdminKey.objects.create(channel=channel)
        assert key.key is not None
        assert len(key.key) == 64  # SHA256 hex digest

    def test_key_is_unique_per_save(self, channel):
        k1 = APIAdminKey.objects.create(channel=channel)
        k2 = APIAdminKey.objects.create(channel=channel)
        assert k1.key != k2.key


# ---------------------------------------------------------------------------
# Revoke
# ---------------------------------------------------------------------------


class TestRevoke:
    def test_create_revoke(self, user):
        revoke = Revoke.objects.create_for_user(user)
        assert revoke.user == user
        assert revoke.created_at is not None

    def test_revoke_str(self, user):
        revoke = Revoke.objects.create_for_user(user)
        assert str(user) in str(revoke)
