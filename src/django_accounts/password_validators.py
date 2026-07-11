# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

from .settings import (
    ACCOUNTS_PASSWORD_LIST_SYMBOLS,
    ACCOUNTS_PASSWORD_MIN_CAPITAL_LETTERS,
    ACCOUNTS_PASSWORD_MIN_NUMBERS,
    ACCOUNTS_PASSWORD_MIN_SPECIAL_SYMBOLS,
)


class CapitalSymbolAndNumbersValidator:
    def __init__(
        self,
        number_of_numbers=ACCOUNTS_PASSWORD_MIN_NUMBERS,
        number_of_capitals=ACCOUNTS_PASSWORD_MIN_CAPITAL_LETTERS,
        number_of_symbols=ACCOUNTS_PASSWORD_MIN_SPECIAL_SYMBOLS,
        symbols=ACCOUNTS_PASSWORD_LIST_SYMBOLS,
    ):
        self.number_of_capitals = number_of_capitals
        self.number_of_symbols = number_of_symbols
        self.number_of_numbers = number_of_numbers
        self.symbols = symbols

    def validate(self, password, user=None):
        capitals = [char for char in password if char.isupper()]
        symbols = [char for char in password if char in self.symbols]
        numbers = [char for char in password if char.isnumeric()]
        if len(capitals) < self.number_of_capitals:
            raise ValidationError(
                _("This password must contain at least %(min_length)d capital letters."),
                code="no_capitals",
                params={"min_length": self.number_of_capitals},
            )
        if len(symbols) < self.number_of_symbols:
            raise ValidationError(
                _("This password must contain at least %(min_length)d symbols."),
                code="no_symbols",
                params={"min_length": self.number_of_symbols},
            )
        if len(numbers) < self.number_of_numbers:
            raise ValidationError(
                _("This password must contain at least %(min_length)d numbers."),
                code="no_numbers",
                params={"min_length": self.number_of_numbers},
            )

    def get_help_text(self):
        return _(
            "Your password must contain at least %(number_of_capitals)d capital letters , %(number_of_symbols) symbols and %(number_of_numbers) numbers"
            % {"number_of_capitals": self.number_of_capitals, "number_of_symbols": self.number_of_symbols}
        )


class SpaceValidator:
    def __init__(self):
        pass

    def validate(self, password, user=None):
        capitals = [char for char in password]
        if " " in capitals:
            raise ValidationError(_("This password should not contain spaces"))

    def get_help_text(self):
        return _("Your password should not contain spaces")
