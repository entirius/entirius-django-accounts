# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from pydantic import BaseModel, ConfigDict, Field


class BaseAddressResponse(BaseModel):
    """Canonical 12-field address shape matching checkout contract."""

    model_config = ConfigDict(from_attributes=True)

    address_id: int = Field(description="Address primary key", examples=[42])
    firstname: str | None = Field(None, description="First name", examples=["Jan"])
    lastname: str | None = Field(None, description="Last name", examples=["Kowalski"])
    street: str = Field(description="Street address", examples=["Marszalkowska 89"])
    city: str = Field(description="City", examples=["Warszawa"])
    postcode: str = Field(description="Postal code", examples=["00-001"])
    country_code: str = Field(description="ISO 2-letter country code", examples=["PL"])
    telephone: str = Field(description="Phone number", examples=["500500500"])
    dialling_code: str = Field(description="International dialling code", examples=["+48"])
    company: str | None = Field(None, description="Company name")
    is_company: bool = Field(description="Whether this is a company address", examples=[False])
    tax_id: str | None = Field(None, description="Tax identification number")
    external_id: str | None = Field(None, description="External system ID")


class AdminAddressResponse(BaseAddressResponse):
    """Admin address with source and default flags."""

    source: str = Field(description="Address origin", examples=["pwa"])
    is_default_billing: bool = Field(description="Default billing address", examples=[True])
    is_default_shipping: bool = Field(description="Default shipping address", examples=[False])
