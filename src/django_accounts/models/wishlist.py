# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import uuid

from django.db import models
from django.db.models import UniqueConstraint
from django_utils.api.exceptions import BadRequest

from django_accounts.models import Customer, ProductRepresentation
from django_accounts.models.managers import WishlistManager


class Wishlist(models.Model):
    uid = models.UUIDField(default=uuid.uuid4, editable=False)
    channel = models.ForeignKey("django_accounts.Channel", on_delete=models.RESTRICT, null=True, blank=True)
    product: "ProductRepresentation" = models.ManyToManyField(
        "ProductRepresentation",
        related_name="accounts_products",
        blank=False,
        through="django_accounts.WishlistProduct",
    )
    customer: "Customer" = models.ForeignKey(
        "django_accounts.Customer", blank=True, null=True, on_delete=models.SET_NULL
    )
    objects = WishlistManager()

    class Meta:
        constraints = [UniqueConstraint(fields=["customer", "channel"], name="unique_wishlist_per_customer")]

    @classmethod
    def create(cls, product: "ProductRepresentation" = None, customer=None, channel=None, *args, **kwargs):
        return cls(product=product, customer=customer, channel=channel, *args, **kwargs)

    def add_customer(self, customer: "Customer"):
        if self.customer is None and customer is not None:
            self.customer = customer
        try:
            self.save()
        except:
            raise BadRequest(message="This customer have already wishlist, no this UID")
        return self


class WishlistProduct(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    wishlist: "Wishlist" = models.ForeignKey(on_delete=models.deletion.CASCADE, to="django_accounts.wishlist")
    product: "ProductRepresentation" = models.ForeignKey(
        on_delete=models.deletion.CASCADE, to="django_accounts.productrepresentation"
    )
    is_external = models.BooleanField(default=False)
    sources = models.JSONField(null=True, blank=True)
    extra = models.JSONField(null=True, blank=True)
    objects = models.Manager()

    def add_extra(self, key: str, value: any):
        if self.extra is None:
            self.extra = {}
        self.extra[key] = value
        self.save()
        return self

    def remove_extra(self, key: str):
        if self.extra is not None and key in self.extra:
            del self.extra[key]
            self.save()
        return self

    def add_source(self, source: str, save: bool = True):
        sources = self.sources if self.sources is not None else []
        sources.append(source)
        sources = list(set(sources))
        self.sources = sources
        if save:
            self.save()
        return self
