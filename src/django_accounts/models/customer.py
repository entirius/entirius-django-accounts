# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import uuid
from typing import TYPE_CHECKING

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from django_accounts.models import Channel, Group


class UserExtensionProxy(get_user_model()):
    @property
    def is_customer(self):
        return hasattr(self, "customer") and self.customer is not None

    class Meta:
        proxy = True


class CustomerManager(models.Manager):
    def create_from_user(
        self,
        user,
        phone=None,
        area_code=None,
        is_active=False,
        created_at=None,
        updated_at=None,
        language=None,
        is_verified=False,
        external_id=None,
        extra=None,
        group=None,
        channel=None,
    ):
        return self.model(
            user=user,
            phone=phone,
            area_code=area_code,
            is_active=is_active,
            is_verified=is_verified,
            created_at=created_at,
            updated_at=updated_at,
            language=language,
            external_id=external_id,
            extra=extra,
            group=group,
            source_channel=channel,
        )


class Customer(models.Model):
    objects = CustomerManager()
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    phone = models.CharField(max_length=32, blank=True, null=True)
    area_code = models.CharField(max_length=32, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    external_id = models.CharField(max_length=32, blank=True, null=True)
    uid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    is_active = models.BooleanField(default=False)
    language = models.ForeignKey("django_regional.Language", on_delete=models.SET_NULL, blank=True, null=True)
    shipping_address = models.ForeignKey(
        "Address", related_name="customer_shipping", null=True, blank=True, on_delete=models.SET_NULL
    )
    billing_address = models.ForeignKey(
        "Address", related_name="customer_billing", null=True, blank=True, on_delete=models.SET_NULL
    )
    is_verified = models.BooleanField(default=False)
    extra = models.JSONField(null=True, blank=True)
    last_session_ip = models.GenericIPAddressField(null=True, blank=True)
    last_session_country = models.ForeignKey(
        "django_regional.Country", null=True, blank=True, on_delete=models.SET_NULL
    )
    group: "Group" = models.ForeignKey("django_accounts.Group", blank=True, null=True, on_delete=models.SET_NULL)
    source_channel: "Channel" = models.ForeignKey(
        "django_accounts.Channel", related_name="customers_source", blank=True, null=True, on_delete=models.SET_NULL
    )
    blacklist_channels = models.ManyToManyField(
        "django_accounts.Channel", related_name="customers_blacklist", blank=True
    )

    class Sex(models.TextChoices):
        MALE = "male", _("Male")
        FEMALE = "female", _("Female")
        OTHER = "other", _("Other")

    sex = models.CharField(null=True, blank=True, max_length=6, choices=Sex.choices)

    class Meta:
        indexes = [
            models.Index(fields=["-created_at"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["is_verified"]),
            models.Index(fields=["source_channel"]),
            models.Index(fields=["group"]),
        ]

    @property
    def email(self):
        valid = self.user.emailaddress_set.filter(primary=True, verified=True).first()
        if valid is not None:
            return valid
        else:
            primary = self.user.emailaddress_set.filter(primary=True).first()
            if primary is not None:
                return primary
            else:
                return self.user.emailaddress_set.first()

    @property
    def first_name(self):
        return self.user.first_name

    @property
    def last_name(self):
        return self.user.last_name

    def check_blacklist(self):
        if self.source_channel:
            for channel in self.blacklist_channels.all():
                if channel == self.source_channel:
                    self.blacklist_channels.remove(channel)

    def __str__(self):
        return f"{self.user}"
