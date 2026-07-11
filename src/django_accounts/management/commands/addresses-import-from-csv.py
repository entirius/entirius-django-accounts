# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import os
from argparse import BooleanOptionalAction

from django.conf import settings
from django.core.management.base import BaseCommand

from django_accounts.enums import AddressesImportBy
from django_accounts.worker import import_addresses_from_csv


class Command(BaseCommand):
    help = "Import addresses from CSV. Choose by_external_id or by_email. Default by_email."

    def add_arguments(self, parser):
        parser.add_argument("--file_path", type=str)
        parser.add_argument("--by_external_id", type=bool, action=BooleanOptionalAction)
        parser.add_argument("--by_email", type=bool, action=BooleanOptionalAction, help="This option is default")

    def handle(self, *args, **options):
        file_path = options["file_path"]
        find_by = AddressesImportBy.map(options["by_email"], options["by_external_id"])

        if file_path is None:
            file_path = os.path.join(settings.IMPORT_DIR, "accounts/addresses.csv")
        errors = 0
        number_addresses_csv = 0
        try:
            errors, number_addresses_csv = import_addresses_from_csv(file_path=file_path, find_by=find_by)
        except Exception as e:
            print(f"{e}")

        print(f"Zostało utworzonych {number_addresses_csv - errors} na {number_addresses_csv} z pliku {file_path}")
