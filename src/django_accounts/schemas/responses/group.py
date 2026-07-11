# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class GroupResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str = Field(description="Group code", examples=["b2b"])
    name: str = Field(description="Group display name", examples=["Business"])
    is_active: bool = Field(description="Whether group is active", examples=[True])
    created_at: datetime = Field(description="Creation timestamp")
    customers_count: int = Field(0, description="Number of customers in this group", examples=[42])
