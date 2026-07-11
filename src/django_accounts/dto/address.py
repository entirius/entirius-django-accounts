# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from dataclasses import asdict
from typing import ClassVar

from marshmallow import Schema, ValidationError
from marshmallow_dataclass import dataclass


@dataclass
class Address:
    street: str | None = None
    city: str | None = None
    postcode: str | None = None
    telephone: str | None = None
    dialling_code: str | None = None
    country_code: str | None = None
    firstname: str | None = None
    lastname: str | None = None
    company: str | None = None
    is_company: bool | None = None
    tax_id: str | None = None
    Schema: ClassVar[type[Schema]] = Schema

    @staticmethod
    def validate_address_data(data, **kwargs):
        def validate_fields(data, fields_list):
            errors_field = []
            for field_name in fields_list:
                if field_name in data and not data[field_name]:
                    errors_field.append(field_name)
            if errors_field:
                raise ValidationError(f"{', '.join(errors_field)} is required")

        def validate_company(data, fields_list):
            errors_field = []
            if data.get("is_company", None):
                for field_name in fields_list:
                    if field_name in data and not data[field_name]:
                        errors_field.append(field_name)
                if errors_field:
                    raise ValidationError(f"{', '.join(errors_field)} is required for company")

        validate_fields(data, ["street", "city", "postcode", "country_code", "telephone", "dialling_code"])
        validate_company(data, ["is_company", "company", "tax_id"])

    def __post_init__(self, *args, **kwargs):
        if self.country_code is not None:
            self.country_code = self.country_code.upper()

        if self.dialling_code is not None:
            if not self.dialling_code.startswith("+"):
                self.dialling_code = f"+{self.dialling_code}"

    # noinspection PyDataclass
    def asdict(self) -> dict:
        return asdict(self)
