# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import json
from dataclasses import field
from itertools import groupby
from typing import ClassVar

from marshmallow import Schema, fields, pre_load
from marshmallow_dataclass import dataclass

from django_accounts.models import Customer


@dataclass
class Sorter:
    order: str
    Schema: ClassVar[type[Schema]] = Schema


@dataclass
class FieldSorter(Sorter):
    field: str
    Schema: ClassVar[type[Schema]] = Schema


@dataclass
class Query:
    sort: list[FieldSorter] | None = None
    Schema: ClassVar[type[Schema]] = Schema

    @pre_load
    def handle_sort(self, data, **kwargs):
        if "sort" in data:
            result = {**data}
            result["sort"] = [json.loads(elem) for elem in result.get("sort")]
            return result
        return data

    @pre_load
    def handle_parameter_list(self, data, **kwargs):
        """Aggregate values from list like parameters, for example from sku and sku[], into one field"""
        key_func = lambda x: x.strip("[]")
        grouped = groupby(sorted(data, key=key_func), key=key_func)
        result = {}
        for key, group in grouped:
            acc = []
            for elem in group:
                acc.extend(data.getlist(elem))

            field = self.declared_fields.get(key)
            if field is None:
                continue
            if isinstance(field, fields.List):
                result[key] = acc
            else:
                result[key] = acc[0]

        return result


@dataclass
class ResetPasswordRequestData:
    email: str
    Schema: ClassVar[type[Schema]] = Schema


@dataclass
class PatchProfileRequestData:
    firstname: str | None
    lastname: str | None
    sex: Customer.Sex | None = field(metadata=dict(by_value=True))
    last_session_ip: str | None
    last_session_country: str | None
    Schema: ClassVar[type[Schema]] = Schema
