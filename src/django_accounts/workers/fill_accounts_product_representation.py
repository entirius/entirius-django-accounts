# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from tqdm import tqdm

from django_accounts.dto.product_representation import ProductRepresentation
from django_accounts.models import Channel
from django_accounts.models import ProductRepresentation as ProductRepresentationModel


def fill_accounts_product_representation_from_pim(pim_shop_idx: str):
    try:
        from django_pim.models import ConfigurableLink, Product, RealProduct, Shop
    except ImportError:
        raise Exception("fill_accounts_product_representation_from_pim does not have access to django_pim module")

    if not pim_shop_idx:
        pim_shop_idxs = Shop.objects.all().values_list("idx", flat=True)
    elif isinstance(pim_shop_idx, str):
        pim_shop_idxs = [pim_shop_idx]
    elif isinstance(pim_shop_idx, list):
        pim_shop_idxs = pim_shop_idx
    else:
        raise ValueError("should happen")

    try:
        products = []
        for pim_shop_idx in pim_shop_idxs:
            print(f"Processing shop with idx {pim_shop_idx}")
            try:
                channel = Channel.objects.get(idx=pim_shop_idx)
            except Channel.DoesNotExist:
                print(f"Channel with idx {pim_shop_idx} does not exist. Skipping.")
                continue

            pim_products: list[Product] = Product.objects.filter(shop__idx=pim_shop_idx)
            for pim_product in tqdm(pim_products):
                product = ProductRepresentation(sku=pim_product.sku, name_t9n=pim_product.name_t9n_json)
                products.append(product)
            ProductRepresentationModel.bulk_update_or_create(products, channel=channel)
    except Exception as e:
        raise e
