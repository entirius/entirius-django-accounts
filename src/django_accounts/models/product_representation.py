# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import tqdm
from django.db import IntegrityError, models
from django.db.models import UniqueConstraint
from idx_normalizator import validate_sku
from process_logger import ProcessLogger

from django_accounts.dto.product_representation import (
    ProductRepresentation as ProductRepresentationDTO,
)
from django_accounts.models.channel import Channel
from django_accounts.settings import T9N_DEFAULT_LANG

logger_process = ProcessLogger("FILL_ACCOUNTS_PRODUCT_REPRESENTATION")


class ProductRepresentation(models.Model):
    sku = models.CharField(db_index=True, max_length=128, null=False)
    name_t9n = models.JSONField(null=True, blank=True)
    channel: "Channel" = models.ForeignKey(
        "django_accounts.Channel",
        related_name="accounts_products_representation_channel",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        default=None,
    )
    objects = models.Manager()

    def save(self, *args, **kwargs):
        validate_sku(self.sku)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.sku}"

    class Meta:
        ordering = ["sku"]
        verbose_name_plural = "products representations"
        constraints = [UniqueConstraint(fields=["sku", "channel"], name="unique_product_representation_per_channel")]

    @property
    def name(self):
        return self.name_lang(lang=T9N_DEFAULT_LANG)

    def name_lang(self, lang):
        langs = [lang]
        if lang != T9N_DEFAULT_LANG:
            langs.append(T9N_DEFAULT_LANG)

        for lang in langs:
            if self.name_t9n is None:
                return self.sku
            val = dict(self.name_t9n).get(lang, None)
            if val is not None:
                val = str(val)
                val = val.strip()
                if len(val) > 0:
                    return val
        return self.sku

    @staticmethod
    def bulk_update_or_create(products: list[ProductRepresentationDTO], channel) -> tuple:
        logger_process.info(f"Accounts Product Bulk Save is starting for {len(products)} products")

        records_to_update = []
        records_to_create = []
        fields_to_update = ["name_t9n"]

        cnt = 0
        total = len(products)

        print("Total products: ", total)
        for product in tqdm.tqdm(products):
            cnt += 1

            kwargs = {}
            find = ProductRepresentation.objects.filter(sku=product.sku, channel=channel).first()

            if find is None:
                records_to_create.append(
                    ProductRepresentation(sku=product.sku, name_t9n=product.name_t9n, channel=channel, **kwargs)
                )
            else:
                records_to_update.append(
                    ProductRepresentation(
                        id=find.id, sku=product.sku, name_t9n=product.name_t9n, channel=channel, **kwargs
                    )
                )
            if cnt % 1000 == 0:
                logger_process.info(f"Accounts Product Bulk Save collecting progress {cnt} / {total}")
        logger_process.info(f"Accounts Product Bulk Save starting bulk update for {len(records_to_update)} products")

        print("Total products to update: ", len(records_to_update))
        # updating data
        try:
            ProductRepresentation.objects.bulk_update(records_to_update, ["sku"] + fields_to_update, batch_size=10000)
        except IntegrityError:
            error_list = []
            for record_to_update in records_to_update:
                try:
                    record_to_update.save(update_fields=["sku"] + fields_to_update)
                except IntegrityError as e:
                    error_sku_data = {
                        "sku": record_to_update.sku,
                        "channel": record_to_update.channel.idx,
                        "message": str(e),
                    }
                    error_list.append(error_sku_data)
            logger_process.error(
                "List of errors during updating Accounts ProductRepresentation",
                extra={"details": {"error_list": error_list}},
            )
        logger_process.info(f"Accounts Product Bulk Save starting bulk create for {len(records_to_create)} products")

        print("Total products to create: ", len(records_to_create))
        # creating data
        try:
            ProductRepresentation.objects.bulk_create(records_to_create, batch_size=1000)
        except IntegrityError:
            error_list = []
            for record_to_create in records_to_create:
                try:
                    record_to_create.save()
                except IntegrityError as e:
                    error_sku_data = {
                        "sku": record_to_create.sku,
                        "channel": record_to_create.channel.idx,
                        "message": str(e),
                    }
                    error_list.append(error_sku_data)
            logger_process.error(
                "List of errors during creating Accounts ProductRepresentation",
                extra={"details": {"error_list": error_list}},
            )

        logger_process.info("Accounts Product Bulk Save is done")
        return len(records_to_create), len(records_to_update)
