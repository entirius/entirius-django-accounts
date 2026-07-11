# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import os

from django.conf import settings
from django.core.management.base import BaseCommand

from django_accounts.worker import import_accounts_from_csv


class Command(BaseCommand):
    help = "Import accounts from CSV"

    def add_arguments(self, parser):
        parser.add_argument("--file_path", type=str)

    def handle(self, *args, **options):
        file_path = options["file_path"]

        if file_path is None:
            file_path = os.path.join(settings.IMPORT_DIR, "accounts/accounts.csv")
        errors = 0
        number_accounts_csv = 0
        try:
            errors, number_accounts_csv = import_accounts_from_csv(file_path=file_path)
        except Exception as e:
            print(f"{e}")

        print(f"Zostało utworzonych {number_accounts_csv - errors} na {number_accounts_csv} z pliku {file_path}")
