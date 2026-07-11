# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from typing import TYPE_CHECKING

from django.contrib.auth import get_user_model
from django.db import models

if TYPE_CHECKING:
    User = get_user_model()


class RevokeManager(models.Manager):
    def create_for_user(self, user: "User"):
        return self.create(user=user)


class Revoke(models.Model):
    """Keeps information about when was the last time a user requested logout"""

    objects = RevokeManager()
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.user} at {self.created_at}"
