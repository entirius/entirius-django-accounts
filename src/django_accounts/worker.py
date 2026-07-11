# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from django_accounts.enums import AddressesImportBy
from django_accounts.services.accounts_service import (
    creating_addresses_for_each_line,
    creating_in_db_for_each_line,
    read_from_csv,
)


def import_accounts_from_csv(file_path: str):
    data, msg = read_from_csv(file_path, "|")
    errors, number_accounts_csv = creating_in_db_for_each_line(data)
    return errors, number_accounts_csv


def import_addresses_from_csv(file_path: str, find_by: int = AddressesImportBy.EMAIL):
    data, msg = read_from_csv(file_path)
    errors, number_addresses_csv = creating_addresses_for_each_line(data, find_by)
    return errors, number_addresses_csv
