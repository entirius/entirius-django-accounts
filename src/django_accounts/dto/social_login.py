# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from marshmallow_dataclass import add_schema, dataclass


@dataclass
class SocialLoginProviders:
    provider: str
    is_enabled: bool
    name: str
    client_id: str
    key: str
    callback_url: str
    front_url: dict


@add_schema
@dataclass
class SocialLoginParams:
    lang: str
    redirect_url: str | None = None
