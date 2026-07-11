# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Admin query service for accounts module."""

from django.db.models import Count, Q, QuerySet

from django_accounts.models import Channel, Customer, Group
from django_accounts.models.address import Address, AddressSourceEnum

ORDERING_ALLOWLIST = {
    "created_at": "created_at",
    "-created_at": "-created_at",
    "updated_at": "updated_at",
    "-updated_at": "-updated_at",
    "email": "user__email",
    "-email": "-user__email",
}

_SOURCE_LABELS = {e.value: e.name.lower() for e in AddressSourceEnum}


class CustomerNotFound(Exception):
    """Raised when a customer UID does not match any record."""


def list_customers(
    *,
    search: str | None = None,
    group: str | None = None,
    source_channel: str | None = None,
    is_active: bool | None = None,
    is_verified: bool | None = None,
    ordering: str | None = None,
) -> QuerySet:
    qs = Customer.objects.select_related("user", "group", "source_channel")

    if search:
        qs = qs.filter(
            Q(user__email__icontains=search)
            | Q(user__first_name__icontains=search)
            | Q(user__last_name__icontains=search)
        )
    if group:
        qs = qs.filter(group__code=group)
    if source_channel:
        qs = qs.filter(source_channel__idx=source_channel)
    if is_active is not None:
        qs = qs.filter(is_active=is_active)
    if is_verified is not None:
        qs = qs.filter(is_verified=is_verified)

    order_field = ORDERING_ALLOWLIST.get(ordering or "-created_at", "-created_at")
    return qs.order_by(order_field)


def get_customer_detail(uid: str) -> Customer:
    """Fetch single customer with all related data prefetched.

    Raises CustomerNotFound if uid does not match any record.
    """
    try:
        return (
            Customer.objects.select_related(
                "user",
                "group",
                "source_channel",
                "language",
                "billing_address",
                "shipping_address",
                "last_session_country",
            )
            .prefetch_related("blacklist_channels", "addresses")
            .annotate(wishlist_items_count=Count("wishlist__wishlistproduct"))
            .get(uid=uid)
        )
    except Customer.DoesNotExist as exc:
        raise CustomerNotFound(f"Customer with uid '{uid}' not found.") from exc


def serialize_customer_list_item(customer: Customer) -> dict:
    # Uses customer.user.email (Django User field) intentionally.
    # Do NOT use customer.email — that's a @property querying allauth EmailAddress (N+1).
    return {
        "uid": str(customer.uid),
        "email": customer.user.email,
        "firstname": customer.user.first_name,
        "lastname": customer.user.last_name,
        "is_active": customer.is_active,
        "is_verified": customer.is_verified,
        "group": customer.group.code if customer.group else None,
        "source_channel": customer.source_channel.idx if customer.source_channel else None,
        "created_at": customer.created_at,
    }


def serialize_customer_detail(customer: Customer) -> dict:
    # Uses customer.user.email — see comment in serialize_customer_list_item.
    addresses = customer.addresses.all()  # reads from prefetch cache, no extra query
    return {
        "uid": str(customer.uid),
        "email": customer.user.email,
        "firstname": customer.user.first_name,
        "lastname": customer.user.last_name,
        "phone": customer.phone,
        "dialling_code": customer.area_code,
        "sex": customer.sex,
        "language": customer.language.iso2 if customer.language else None,
        "is_active": customer.is_active,
        "is_verified": customer.is_verified,
        "group": {"code": customer.group.code, "name": customer.group.name} if customer.group else None,
        "source_channel": (
            {"idx": customer.source_channel.idx, "label": customer.source_channel.label}
            if customer.source_channel
            else None
        ),
        "blacklist_channels": [{"idx": ch.idx, "label": ch.label} for ch in customer.blacklist_channels.all()],
        "last_session_ip": str(customer.last_session_ip) if customer.last_session_ip else None,
        "last_session_country": customer.last_session_country.code if customer.last_session_country else None,
        "created_at": customer.created_at,
        "updated_at": customer.updated_at,
        "external_id": customer.external_id,
        # extra is returned unfiltered for admin users (intentional — admins need full visibility).
        # The v1 public profile applies SPECIFY_KEYS_EXTRA_PROFILE_DATA_IN_API whitelist.
        "extra": customer.extra,
        "addresses": [_serialize_admin_address(addr, customer) for addr in addresses],
        "addresses_count": len(addresses),
        "wishlist_items_count": getattr(customer, "wishlist_items_count", 0),
    }


def _serialize_admin_address(address: Address, customer: Customer) -> dict:
    return {
        "address_id": address.pk,
        "firstname": address.firstname,
        "lastname": address.lastname,
        "street": address.street,
        "city": address.city,
        "postcode": address.postcode,
        "country_code": address.country_code,
        "telephone": address.telephone,
        "dialling_code": address.dialling_code,
        "company": address.company,
        "is_company": address.is_company,
        "tax_id": address.tax_id,
        "external_id": address.external_id,
        "source": _SOURCE_LABELS.get(address.source, "unknown"),
        "is_default_billing": customer.billing_address_id == address.pk,
        "is_default_shipping": customer.shipping_address_id == address.pk,
    }


def list_groups() -> QuerySet:
    return Group.objects.annotate(customers_count=Count("customer")).order_by("code")


def serialize_group(group: Group) -> dict:
    return {
        "code": group.code,
        "name": group.name,
        "is_active": group.is_active,
        "created_at": group.created_at,
        "customers_count": getattr(group, "customers_count", 0),
    }


def list_channels() -> QuerySet:
    return Channel.objects.select_related("language").order_by("pk")


def serialize_channel(channel: Channel) -> dict:
    return {"idx": channel.idx, "label": channel.label, "language": channel.language.iso2 if channel.language else None}
