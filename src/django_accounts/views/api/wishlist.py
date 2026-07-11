# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from django.views.decorators.csrf import csrf_exempt
from django_utils.api.decorators import (
    api_view,
    authenticate,
    parse_body,
    parse_parameters,
    require_http_method,
)
from django_utils.api.exceptions import BadRequest, NotFound
from django_utils.api.responses import Response

from django_accounts.dto.wishlist import (
    GetWishlistParams,
    WishlistExtraRequestPayload,
    WishlistParams,
    WishlistRequestPayload,
)
from django_accounts.models import ProductRepresentation, Wishlist, WishlistProduct
from django_accounts.utils.decorators import channel_view


def build_wishlist_data(data: dict, wishlist_products: list[WishlistProduct], language: str = None):
    if wishlist_products:
        data["products"] = [
            {
                "sku": each.product.sku,
                "is_external": each.is_external,
                "extra": each.extra,
                "name": each.product.name_lang(language),
            }
            for each in wishlist_products
        ]
    return data


@api_view
@csrf_exempt
@authenticate
@channel_view
@require_http_method("POST", "DELETE", "PATCH")
def wishlist_product(request, *args, **kwargs):
    def get_wish_list(request, params, channel, create_if_no_exists=False):
        customer = request.user.customer if (request.user is not None and request.user.is_customer) else None
        wishlist = Wishlist.objects.get_record(
            request=request,
            customer=customer,
            wishlist_uid=params.uid,
            channel=channel,
            create_if_no_exists=create_if_no_exists,
        )

        return wishlist

    @parse_parameters(WishlistParams.Schema())
    @parse_body(WishlistRequestPayload.Schema)
    def delete(request, params: WishlistParams, body: WishlistRequestPayload):
        wishlist = get_wish_list(request, params, request.channel)
        if wishlist is None:
            raise BadRequest(message="Need to provide uid or authorize")
        if body.sku:
            products = ProductRepresentation.objects.filter(sku__in=body.sku, channel=request.channel)
            if wishlist:
                wishlist.product.remove(*products)

        data = {}
        if wishlist.product:
            wishlist_products = WishlistProduct.objects.filter(wishlist=wishlist)
            data = build_wishlist_data(data, wishlist_products, params.language or request.channel.language.iso2)
        data["uid"] = wishlist.uid
        return Response(
            data,
            message=f"Products {', '.join(products.values_list('sku', flat=True))} from wishlist successfully deleted",
        )

    @parse_parameters(WishlistParams.Schema())
    @parse_body(WishlistRequestPayload.Schema)
    def post(request, params: WishlistParams, body: WishlistRequestPayload):
        wishlist = get_wish_list(request, params, request.channel, True)
        added_skus = []
        if body.sku:
            products = ProductRepresentation.objects.filter(sku__in=body.sku, channel=request.channel)
            if products.count() == 0:
                raise BadRequest(message="No SKUs in accounts product representation.")
            wishlist.product.add(*products)
            for product in products:
                added_skus.append(product.sku)

        data = {}
        if wishlist.product:
            wishlist_products = WishlistProduct.objects.filter(wishlist=wishlist)
            data = build_wishlist_data(
                data, wishlist_products, language=params.language or request.channel.language.iso2
            )
        data["uid"] = wishlist.uid
        return Response(data, message=f"Products {', '.join(added_skus)} to wishlist successfully added")

    @parse_parameters(WishlistParams.Schema())
    @parse_body(WishlistExtraRequestPayload.Schema)
    def patch(request, params: WishlistParams, body: WishlistExtraRequestPayload):
        wishlist = get_wish_list(request, params, request.channel)
        if wishlist is None:
            raise BadRequest(message="Need to provide uid or authorize")

        sku_list = []
        skipped = []
        data = {}
        for product in body.products:
            if product.sku:
                wp = WishlistProduct.objects.filter(wishlist=wishlist, product__sku=product.sku).first()
                if wp is None:
                    skipped.append(product.sku)
                    continue
                for key, value in product.extra.items():
                    if value:
                        wp.add_extra(key, value)
                    else:
                        wp.remove_extra(key)
                sku_list.append(product.sku)

        if len(sku_list) == 0:
            raise NotFound(message="Products not found in wishlist")

        wishlist_products = WishlistProduct.objects.filter(wishlist=wishlist)
        data = build_wishlist_data(data, wishlist_products, params.language or request.channel.language.iso2)

        messages = [f"Products {', '.join(sku_list)} in wishlist successfully updated"]
        if len(skipped) > 0:
            messages.append(f"Products {', '.join(skipped)} not found in wishlist")
        return Response(data, messages=messages)

    if request.method == "DELETE":
        return delete(request)
    elif request.method == "POST":
        return post(request)
    elif request.method == "PATCH":
        return patch(request)


@api_view
@csrf_exempt
@authenticate
@channel_view
@require_http_method("GET", "POST")
def wishlist_detail(request, *args, **kwargs):
    def get_wish_list(request, params, channel, create_if_no_exists=False):
        customer = request.user.customer if (request.user is not None and request.user.is_customer) else None
        wishlist = Wishlist.objects.get_record(
            request=request,
            customer=customer,
            wishlist_uid=params.uid,
            channel=channel,
            create_if_no_exists=create_if_no_exists,
        )
        return wishlist

    @parse_parameters(GetWishlistParams.Schema())
    def get(request, params: GetWishlistParams):
        wishlist = get_wish_list(request, params, request.channel)
        if wishlist is None:
            raise BadRequest(message="Need to provide uid or authorize")
        customer = request.user.customer if (request.user is not None and request.user.is_customer) else None
        if wishlist.customer is not None and wishlist.customer != customer:
            raise BadRequest(message="Authorize to view customer wishlist")
        sorting_params = []
        data = {}

        if wishlist.product:
            wishlist_products = WishlistProduct.objects.filter(wishlist=wishlist)
            if params.sort:
                for sorter in getattr(params, "sort", []):
                    if sorter.field == "created_at":
                        sorter_direction = "-" if sorter.order == "DESC" else ""
                        sorting_params.append(f"{sorter_direction}{sorter.field}")
            else:
                sorting_params = ["-created_at"]

            if params.name:
                wishlist_products = wishlist_products.filter(product__name__contains=params.name)

            data = build_wishlist_data(
                data, wishlist_products, language=params.language or request.channel.language.iso2
            )
        data["uid"] = wishlist.uid
        return Response(data)

    @parse_parameters(WishlistParams.Schema())
    def post(request, params: WishlistParams):
        wishlist = Wishlist.objects.guest_wishlist_to_customer(request, params)
        wishlist_products = WishlistProduct.objects.filter(wishlist=wishlist)
        data = {}
        data = build_wishlist_data(data, wishlist_products, language=params.language or request.channel.language.iso2)
        data["uid"] = wishlist.uid
        return Response(data, message="Guest wishlist successfully saved into customer wishlist")

    if request.method == "GET":
        return get(request)
    elif request.method == "POST":
        return post(request)
