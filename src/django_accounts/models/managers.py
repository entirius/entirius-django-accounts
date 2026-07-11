# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from typing import TYPE_CHECKING, Optional

from django.core.exceptions import ValidationError
from django.db import models
from django_utils.api.exceptions import BadRequest

if TYPE_CHECKING:
    from django_accounts.models.wishlist import Wishlist


class WishlistManager(models.Manager):
    def get_record(
        self, request, customer=None, wishlist_uid=None, channel=None, create_if_no_exists=False
    ) -> Optional["Wishlist"]:

        # Jeżeli nie jest podane wishlist_uid i customer utwórz wishliste
        if not wishlist_uid and not customer:
            if create_if_no_exists:
                record = self.create(customer=customer, channel=channel)
                return record
            else:
                raise BadRequest(message="You need to specify wishlist_uid or authorize")

        # Jeżeli jest customer to sprawdza czy jest uid i jak ten uid nie ma customera to mu go przypisuje,
        if customer:
            record = self.filter(customer=customer, channel=channel).first()

            if wishlist_uid:
                try:
                    record, created = self.get_or_create(uid=wishlist_uid)
                except ValidationError:
                    raise BadRequest(message="Incorrect UUID")
                if record.customer is None:
                    record = record.add_customer(customer)
            elif create_if_no_exists and not record:
                try:
                    record = self.create(customer=customer, channel=channel)
                except:
                    raise BadRequest(message="This customer have already wishlist, no this UID")

        # Jeżeli nie ma customera, szuka wishliste o danym uid lub tworzy o tym uid
        else:
            try:
                record, created = self.get_or_create(uid=wishlist_uid)
            except ValidationError:
                raise BadRequest(message="Incorrect UUID")
        return record

    def guest_wishlist_to_customer(self, request, params):
        customer = request.user.customer if (request.user is not None and request.user.is_customer) else None
        if not customer or not params.uid:
            raise BadRequest(message="You need to provide guest wishlist uid and authorize")
        record_logged, created = self.get_or_create(customer=customer, channel=request.channel)
        record_quest, created = self.get_or_create(uid=params.uid)
        if record_quest.uid != record_logged.uid:
            record_logged.product.add(*record_quest.product.all())
            record_quest.delete()
        return record_logged
