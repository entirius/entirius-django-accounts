# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from time import time

from django.core.files.storage import FileSystemStorage
from django.db import models
from django.db.models import TextChoices
from django.utils.translation import gettext_lazy as _

from django_accounts import settings


def customer_directory_path(instance, filename):
    filename = str(int(time())) + "-" + filename
    return f"{instance.customer.uid}/{filename}"


def customer_storage():
    return FileSystemStorage(location=settings.CUSTOMER_DIR)


class FileType(TextChoices):
    DEFAULT = "default", _("Default")
    ADDRESS_ATTACHMENT = "address_attachment", _("Address Attachment")


class File(models.Model):
    objects = models.Manager()
    customer = models.ForeignKey(
        "Customer", related_name="files", verbose_name="customer", null=False, blank=False, on_delete=models.CASCADE
    )
    file_type = models.CharField(max_length=128, default=FileType.DEFAULT, choices=FileType.choices)
    upload = models.FileField(upload_to=customer_directory_path, storage=customer_storage)
    name = models.TextField(blank=True, null=True, default=None)
    label = models.CharField(max_length=256, blank=True, null=True, default=None)

    def save(self, *args, **kwargs):
        self.name = self.upload.name
        super().save(*args, **kwargs)

    @property
    def get_download_url(self):
        return f"/customer/{self.customer.uid}/file/{self.pk}"

    @property
    def as_dict(self):
        return {"file_id": self.pk, "name": self.name, "label": self.label, "path": self.get_download_url}


class AddressFile(File):
    address = models.ForeignKey(
        "Address", related_name="files", verbose_name="address", null=False, blank=False, on_delete=models.CASCADE
    )

    @property
    def get_download_url(self):
        return f"/customer/{self.customer.uid}/addresses/files/?id={self.address.pk}&file_id={self.pk}"

    def save(self, *args, **kwargs):
        self.customer = self.address.customer
        self.file_type = FileType.ADDRESS_ATTACHMENT
        super().save(*args, **kwargs)
