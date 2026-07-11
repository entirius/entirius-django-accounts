# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.


class AddressesImportBy:
    EMAIL = 1
    EXTERNAL_ID = 2

    @staticmethod
    def map(by_email: bool, by_external_id: bool) -> int:
        if by_email:
            return AddressesImportBy.EMAIL
        if by_external_id:
            return AddressesImportBy.EXTERNAL_ID
        return AddressesImportBy.EMAIL


class AssignAddress:
    SHIPPING = 1
    BILLING = 2
    BOTH = 3

    @staticmethod
    def map(value, default=None):
        match value:
            case "1":
                return AssignAddress.SHIPPING
            case "2":
                return AssignAddress.BILLING
            case "3":
                return AssignAddress.BOTH
            case _:
                return default
