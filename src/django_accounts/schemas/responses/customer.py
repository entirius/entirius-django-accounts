# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from django_accounts.schemas.responses.address import AdminAddressResponse


class CustomerListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    uid: str = Field(description="Customer UUID", examples=["550e8400-e29b-41d4-a716-446655440000"])
    email: str = Field(description="Email address", examples=["jan@example.com"])
    firstname: str = Field(description="First name", examples=["Jan"])
    lastname: str = Field(description="Last name", examples=["Kowalski"])
    is_active: bool = Field(description="Whether customer is active", examples=[True])
    is_verified: bool = Field(description="Whether customer is verified", examples=[True])
    group: str | None = Field(None, description="Group code", examples=["b2b"])
    source_channel: str | None = Field(None, description="Source channel idx", examples=["default-europe"])
    created_at: datetime = Field(description="Registration timestamp")


class CustomerGroupEmbed(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str = Field(description="Group code", examples=["b2b"])
    name: str = Field(description="Group display name", examples=["Business"])


class CustomerChannelEmbed(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    idx: str = Field(description="Channel identifier", examples=["default-europe"])
    label: str = Field(description="Channel display name", examples=["Europe"])


class CustomerDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    uid: str = Field(description="Customer UUID")
    email: str = Field(description="Email address")
    firstname: str = Field(description="First name")
    lastname: str = Field(description="Last name")
    phone: str | None = Field(None, description="Phone number")
    dialling_code: str | None = Field(None, description="International dialling code")
    sex: str | None = Field(None, description="Gender", examples=["male"])
    language: str | None = Field(None, description="Language ISO2 code", examples=["pl"])
    is_active: bool = Field(description="Whether customer is active")
    is_verified: bool = Field(description="Whether customer is verified")
    group: CustomerGroupEmbed | None = Field(None, description="Customer group")
    source_channel: CustomerChannelEmbed | None = Field(None, description="Registration channel")
    blacklist_channels: list[CustomerChannelEmbed] = Field(default_factory=list, description="Blocked channels")
    last_session_ip: str | None = Field(None, description="Last session IP address")
    last_session_country: str | None = Field(None, description="Last session country code")
    created_at: datetime = Field(description="Registration timestamp")
    updated_at: datetime = Field(description="Last update timestamp")
    external_id: str | None = Field(None, description="External system ID")
    extra: dict | None = Field(None, description="Extra profile data")
    addresses: list[AdminAddressResponse] = Field(default_factory=list, description="Customer addresses")
    addresses_count: int = Field(0, description="Total number of addresses")
    wishlist_items_count: int = Field(0, description="Total wishlist items across all channels")
