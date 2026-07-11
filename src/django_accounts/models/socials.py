# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from django.db import models


class SocialLoginProviders(models.Model):
    channel = models.ForeignKey("django_accounts.Channel", on_delete=models.CASCADE, blank=True, null=True)
    PROVIDER_CHOICES = (("google", "Google"), ("facebook", "Facebook"))
    is_enabled = models.BooleanField(default=False)
    provider = models.CharField(max_length=32, choices=PROVIDER_CHOICES, blank=False, null=False)
    name = models.CharField(max_length=32, blank=True, null=True)
    client_id = models.CharField(max_length=256)
    key = models.CharField(max_length=256)
    callback_url = models.CharField(max_length=256)
    front_url = models.JSONField(
        default=dict, blank=True, help_text='Multilingual URLs, e.g. {"pl": "https://...", "en": "https://..."}'
    )
    allowed_origins = models.JSONField(
        default=list,
        blank=True,
        help_text="Lista dozwolonych domen dla redirect_url, Lista: []",
    )
    objects = models.Manager()

    def __str__(self):
        return f"{self.provider}"

    class Meta:
        verbose_name = "Social Login - Provider"
        verbose_name_plural = "Social Login - Providers"
