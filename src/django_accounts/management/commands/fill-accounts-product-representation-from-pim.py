# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from django.core.management.base import BaseCommand

from django_accounts.workers.fill_accounts_product_representation import fill_accounts_product_representation_from_pim


class Command(BaseCommand):
    help = "Fill Accounts ProductRepresentation data from PIM"

    def add_arguments(self, parser):
        parser.add_argument("--pim_shop_idx", type=str, default=None, help="PIM shop idx (required)")

    def handle(self, *args, **options):
        pim_shop_idx = options["pim_shop_idx"]
        fill_accounts_product_representation_from_pim(pim_shop_idx=pim_shop_idx)
