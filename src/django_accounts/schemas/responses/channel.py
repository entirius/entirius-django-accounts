# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from pydantic import BaseModel, ConfigDict, Field


class ChannelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    idx: str = Field(description="Channel identifier", examples=["default-europe"])
    label: str = Field(description="Channel display name", examples=["Europe"])
    language: str | None = Field(None, description="Default language ISO2 code", examples=["en"])
