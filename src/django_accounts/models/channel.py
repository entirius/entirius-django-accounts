# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from typing import TYPE_CHECKING

from django.db import models
from idx_normalizator import validate_idx

if TYPE_CHECKING:
    from django_regional.models import Language


class Channel(models.Model):
    idx = models.CharField(max_length=128, blank=False, null=False, unique=True)
    label = models.CharField(max_length=128, blank=False, null=False, default="", unique=True)
    language: "Language" = models.ForeignKey(
        "django_regional.Language",
        related_name="default_channels_accounts",
        verbose_name="default language",
        help_text="Used for for social login.",
        null=False,
        blank=False,
        on_delete=models.PROTECT,
    )
    objects = models.Manager()

    def save(self, *args, **kwargs):
        validate_idx(str(self.idx))
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.label} [{self.idx}]"

    class Meta:
        ordering = ["pk"]
