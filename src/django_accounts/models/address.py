# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from enum import IntEnum

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django_utils.api.exceptions import BadRequest
from int_enum_choices import IntEnumChoices

from django_accounts import settings


class AddressSourceEnum(IntEnum):
    UNKNOWN = 0
    PWA = 1  # Address from PWA
    MAGENTO = 2  # Address imported from Magento
    EXTERNAL = 3  # Address imported from external source like SAP, ERP
    CSV = 4  # Address imported from CSV


class AddressSource(IntEnumChoices):
    enumClass = AddressSourceEnum

    labels = {
        AddressSourceEnum.UNKNOWN: "Address source unknown",
        AddressSourceEnum.PWA: "Address from PWA",
        AddressSourceEnum.MAGENTO: "Address from Magento2",
        AddressSourceEnum.EXTERNAL: "Address from external source",
        AddressSourceEnum.CSV: "Address from CSV",
    }


class AddressManager(models.Manager):
    @staticmethod
    def make_address_as_default_for_customer(address, customer, address_type="billing", save_as_default=True):
        if save_as_default:
            address_type = f"{address_type}_address"
            setattr(customer, address_type, address)
            customer.save()

    def create_from_dict(self, data, customer):
        field_names = [f.name for f in self.model._meta.fields]
        data = {k: v for k, v in data.items() if k in field_names}
        new = self.model(customer=customer, **data)
        new.save()
        return new

    def check_field_while_updating(self, address_data, address_type, field_names):
        add = list(address_data.items())
        not_editable_fields = []

        if address_type == "billing" and getattr(self, "is_company", None):
            is_invalid = False
            if not settings.BILLING_ADDRESS_EDITABLE:
                not_editable_fields += ["street", "city", "postcode", "country_code", "is_company", "company", "tax_id"]
            if not settings.BILLING_ADDRESS_PHONE_EDITABLE:
                not_editable_fields += ["dialling_code", "telephone"]
            can_be_modified = [x for x in field_names if x not in not_editable_fields]
            if not_editable_fields:
                for string in add:
                    if string[0] in not_editable_fields:
                        is_invalid = True

            if is_invalid:
                raise BadRequest(
                    status="FAIL",
                    message=f"You have entered fields that are not allowed for editing in billing address. The fields allowed for editing are: {', '.join(can_be_modified)}",
                )


class Address(models.Model):
    objects = AddressManager()

    customer = models.ForeignKey(
        "Customer", related_name="addresses", verbose_name="customer", null=False, blank=False, on_delete=models.CASCADE
    )
    firstname = models.CharField(max_length=128, blank=True, null=True, default=None)
    lastname = models.CharField(max_length=128, blank=True, null=True, default=None)
    street = models.CharField(max_length=128, blank=True, null=False, default="")
    city = models.CharField(max_length=128, blank=False, null=False)
    postcode = models.CharField(max_length=32, blank=False, null=False)
    telephone = models.CharField(max_length=64, blank=False, null=False)
    dialling_code = models.CharField(max_length=6, blank=False, null=False, default="")
    country_code = models.CharField(max_length=2, blank=False, null=False, default="")
    company = models.CharField(max_length=256, blank=True, null=True, default=None)
    is_company = models.BooleanField(default=False)
    tax_id = models.CharField(max_length=32, blank=True, null=True, default=None)
    source = models.PositiveSmallIntegerField(
        choices=AddressSource.choices(), blank=False, null=False, default=AddressSourceEnum.PWA
    )
    external_id = models.CharField(max_length=32, blank=True, null=True)

    @property
    def as_dict(self):
        files = self.files.all()
        attachments = []
        for file in files:
            attachments.append(file.as_dict)

        return {
            "address_id": str(self.pk),
            "firstname": self.firstname,
            "lastname": self.lastname,
            "street": self.street,
            "city": self.city,
            "postcode": self.postcode,
            "telephone": self.telephone,
            "dialling_code": self.dialling_code,
            "country_code": self.country_code,
            "is_company": self.is_company,
            "company": self.company,
            "tax_id": self.tax_id,
            "attachments": attachments,
            "external_id": self.external_id,
        }

    def update_from_dict(self, data, customer):
        if self.pk is None:
            raise Exception("Cannot update, record does not exist in the database")
        else:
            for field, value in data.items():
                setattr(self, field, value)
            self.customer = customer
            self.save()
            return self

    def __str__(self):
        if self.firstname or self.lastname:
            return f"{self.firstname} {self.lastname}, {self.street}, {self.city}, {self.postcode}"
        elif self.company:
            return f"{self.company}, {self.street}, {self.city}, {self.postcode}"
        else:
            return f"{self.street}, {self.city}, {self.postcode}"

    def clean(self):
        if (self.firstname is None or self.lastname is None) and self.company is None:
            raise ValidationError("One of firstname/lastname or company can not be null.")
        if self.is_company is True and (self.company is None or self.tax_id is None):
            raise ValidationError("Data for company can not be null.")

    def save(self, *args, **kwargs):
        if self.is_company is None:
            if self.tax_id is not None:
                self.is_company = True
            if self.tax_id is None:
                self.is_company = False
        super().save(*args, **kwargs)

    class Meta:
        ordering = []
        verbose_name_plural = "Addresses"
        constraints = [
            models.CheckConstraint(
                condition=(Q(firstname__isnull=False) & Q(lastname__isnull=False)) | Q(company__isnull=False),
                name="name_or_company_have_to_be_not_null",
            ),
            models.CheckConstraint(
                condition=Q(is_company=False) | (Q(company__isnull=False) & Q(tax_id__isnull=False)),
                name="data_for_company_can_not_be_null",
            ),
        ]
