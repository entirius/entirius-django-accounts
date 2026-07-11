# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import json
from itertools import groupby
from typing import ClassVar

from marshmallow import Schema, fields, pre_load
from marshmallow_dataclass import add_schema, dataclass


@dataclass
class SimpleQuery:
    language: str | None
    Schema: ClassVar[type[Schema]] = Schema


@dataclass
class Sorter:
    order: str
    Schema: ClassVar[type[Schema]] = Schema


@dataclass
class FieldSorter(Sorter):
    field: str
    Schema: ClassVar[type[Schema]] = Schema


@add_schema
@dataclass
class WishlistParams(SimpleQuery):
    uid: str | None
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


@add_schema
@dataclass
class GetWishlistParams(SimpleQuery):
    uid: str | None
    name: str | None
    sort: list[FieldSorter] | None = None
    Schema: ClassVar[type[Schema]] = Schema


@add_schema
@dataclass
class WishlistRequestPayload:
    sku: list[str]
    Schema: ClassVar[type[Schema]] = Schema


@add_schema
@dataclass
class ProductExtraPayload:
    sku: str
    extra: dict
    Schema: ClassVar[type[Schema]] = Schema


@add_schema
@dataclass
class WishlistExtraRequestPayload:
    products: list[ProductExtraPayload]
    Schema: ClassVar[type[Schema]] = Schema
