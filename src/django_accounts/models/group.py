# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from django.db import models


class Group(models.Model):
    objects = models.Manager()
    code = models.CharField(max_length=32, blank=False, null=False, unique=True)
    name = models.CharField(max_length=254, blank=False, null=False, default="", unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name}"
