# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import pytest
from django.core.exceptions import ValidationError

from django_accounts.password_validators import (
    CapitalSymbolAndNumbersValidator,
    SpaceValidator,
)


class TestCapitalSymbolAndNumbersValidator:
    def setup_method(self):
        self.validator = CapitalSymbolAndNumbersValidator()

    def test_valid_password(self):
        self.validator.validate("StrongPass1!")

    def test_no_capital_letters(self):
        with pytest.raises(ValidationError, match="capital"):
            self.validator.validate("weakpass1!")

    def test_no_numbers(self):
        with pytest.raises(ValidationError, match="numbers"):
            self.validator.validate("StrongPass!")

    def test_no_symbols(self):
        with pytest.raises(ValidationError, match="symbols"):
            self.validator.validate("StrongPass1")

    def test_empty_password(self):
        with pytest.raises(ValidationError):
            self.validator.validate("")

    def test_custom_min_capitals(self):
        validator = CapitalSymbolAndNumbersValidator(number_of_capitals=3)
        with pytest.raises(ValidationError, match="capital"):
            validator.validate("ABpass1!")
        validator.validate("ABCpass1!")


class TestSpaceValidator:
    def setup_method(self):
        self.validator = SpaceValidator()

    def test_valid_password_no_spaces(self):
        self.validator.validate("NoSpaces1!")

    def test_password_with_space(self):
        with pytest.raises(ValidationError, match="spaces"):
            self.validator.validate("Has Space1!")
