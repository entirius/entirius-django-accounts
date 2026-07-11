# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import os

from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django_utils.api.decorators import (
    api_view,
    authenticate,
    parse_body,
    parse_parameters,
    require_authentication,
    require_http_method,
)
from django_utils.api.exceptions import Forbidden, NotFound, ValidationError
from django_utils.api.responses import Response

from django_accounts.dto.address import Address as AddressDC
from django_accounts.forms import AddressFileForm
from django_accounts.models import Address, AddressFile, Customer
from django_accounts.utils.address import (
    AddressesDefaultsParams,
    AddressesFilesParams,
    IDParams,
    LazyParams,
)


def check_customer(request, uid):
    customer = request.user.customer
    customer_uid = str(customer.uid)
    if customer_uid != uid:
        raise Forbidden("You are not allowed to access this resource.")


@api_view
@csrf_exempt
@authenticate
@require_authentication
@require_http_method("GET", "PUT", "PATCH", "DELETE")
def customer_addresses(request, uid=None, *args, **kwargs):
    # noinspection PyShadowingNames
    @parse_parameters(IDParams.Schema())
    def _get(request, uid, params: IDParams, *args, **kwargs):
        if params.id:
            try:
                address = Address.objects.get(customer__uid=uid, pk=params.id)
            except ObjectDoesNotExist:
                raise NotFound()
            response = {address.pk: address.as_dict}
        else:
            addresses = Address.objects.filter(customer__uid=uid).order_by("-pk")
            response = {address.pk: address.as_dict for address in addresses}

        return Response(response)

    # noinspection PyShadowingNames
    @parse_body(AddressDC.Schema)
    def _put(request, uid, body: AddressDC, *args, **kwargs):
        AddressDC.validate_address_data(body.asdict())
        address = Address.objects.create_from_dict(body.asdict(), request.user.customer)

        return Response({address.pk: address.as_dict}, message="Address created successfully")

    # noinspection PyShadowingNames
    @parse_body(AddressDC.Schema)
    @parse_parameters(IDParams.Schema())
    def _patch(request, uid, body: AddressDC, params: IDParams, *args, **kwargs):
        if params.id:
            try:
                address = Address.objects.get(customer__uid=uid, pk=params.id)
            except ObjectDoesNotExist:
                raise NotFound()

            AddressDC.validate_address_data(body.asdict())
            address = address.update_from_dict(body.asdict(), request.user.customer)
        else:
            raise NotFound()

        return Response({address.pk: address.as_dict}, message="Address updated successfully")

    # noinspection PyShadowingNames
    @parse_parameters(IDParams.Schema())
    def _delete(request, uid, params: IDParams, *args, **kwargs):
        if params.id:
            try:
                address = Address.objects.get(customer__uid=uid, pk=params.id)
            except ObjectDoesNotExist:
                raise NotFound()
            address.delete()
        else:
            raise NotFound()
        return Response({}, message="Address deleted successfully")

    check_customer(request, uid)
    match request.method:
        case "GET":
            return _get(request, uid, *args, **kwargs)
        case "PUT":
            return _put(request, uid, *args, **kwargs)
        case "PATCH":
            return _patch(request, uid, *args, **kwargs)
        case "DELETE":
            return _delete(request, uid, *args, **kwargs)


@api_view
@csrf_exempt
@authenticate
@require_authentication
@require_http_method("GET", "POST")
def customer_addresses_defaults(request, uid=None, *args, **kwargs):
    # noinspection PyShadowingNames
    @parse_parameters(LazyParams.Schema)
    def _get(request, params: LazyParams, *args, **kwargs):
        response = {"billing_address": None, "shipping_address": None}
        customer: Customer = request.user.customer

        if params.lazy_loading:
            response["billing_address"] = str(customer.billing_address.pk) if customer.billing_address else None
            response["shipping_address"] = str(customer.shipping_address.pk) if customer.shipping_address else None
        else:
            response["billing_address"] = customer.billing_address.as_dict if customer.billing_address else None
            response["shipping_address"] = customer.shipping_address.as_dict if customer.shipping_address else None

        return Response(response)

    # noinspection PyShadowingNames
    @parse_body(AddressesDefaultsParams.Schema())
    @parse_parameters(LazyParams.Schema)
    def _post(request, uid, body: AddressesDefaultsParams, params: LazyParams, *args, **kwargs):
        response = {"billing_address": None, "shipping_address": None}
        customer: Customer = request.user.customer
        save = False

        # Jeśli False to nie zapisuj, jeśli None lub wartosc to nadpisz
        if body.billing_address is not False:
            if body.billing_address and body.billing_address != "":
                try:
                    address = Address.objects.get(customer__uid=uid, pk=body.billing_address)
                except ObjectDoesNotExist:
                    raise NotFound("billing_address")
                customer.billing_address = address
            else:
                customer.billing_address = None
            save = True

        # Jeśli False to nie zapisuj, jeśli None lub wartosc to nadpisz
        if body.shipping_address is not False:
            if body.shipping_address and body.shipping_address != "":
                try:
                    address = Address.objects.get(customer__uid=uid, pk=body.shipping_address)
                except ObjectDoesNotExist:
                    raise NotFound("shipping_address")
                customer.shipping_address = address
            else:
                customer.shipping_address = None
            save = True

        if save:
            customer.save()

        if params.lazy_loading:
            response["billing_address"] = str(customer.billing_address.pk) if customer.billing_address else None
            response["shipping_address"] = str(customer.shipping_address.pk) if customer.shipping_address else None
        else:
            response["billing_address"] = customer.billing_address.as_dict if customer.billing_address else None
            response["shipping_address"] = customer.shipping_address.as_dict if customer.shipping_address else None

        return Response(response)

    check_customer(request, uid)
    match request.method:
        case "GET":
            return _get(request, *args, **kwargs)
        case "POST":
            return _post(request, uid, *args, **kwargs)


@api_view
@csrf_exempt
@require_http_method("POST", "GET")
def customer_addresses_files(request, uid=None, *args, **kwargs):
    @authenticate
    @require_authentication
    @parse_parameters(IDParams.Schema)
    def _post(request, uid, params: IDParams, *args, **kwargs):
        check_customer(request, uid)

        try:
            address = Address.objects.get(pk=params.id)
        except ObjectDoesNotExist:
            raise NotFound(status="address_doesnt_exists")

        if str(address.customer.uid) != uid:
            raise Forbidden(status="address_and_user_unmatched")

        address_file = AddressFile(customer=request.user.customer, address=address)

        form = AddressFileForm(request.POST, request.FILES, instance=address_file)
        if form.is_valid():
            form.save()
            return Response({}, message="File uploaded successfully")
        else:
            raise ValidationError(status="error_validate_file_form", data=form.errors)

    @parse_parameters(AddressesFilesParams.Schema)
    def _get(request, uid, params: AddressesFilesParams, *args, **kwargs):
        try:
            address = Address.objects.get(pk=params.id)
        except ObjectDoesNotExist:
            raise NotFound(status="address_doesnt_exists")

        if str(address.customer.uid) != uid:
            raise Forbidden(status="address_and_user_unmatched")

        try:
            file = AddressFile.objects.get(address=address, pk=params.file_id)
        except ObjectDoesNotExist:
            raise NotFound(status="file_doesnt_exists")

        file_path = file.upload.path
        if os.path.exists(file_path):
            with open(file_path, "rb") as fh:
                response = HttpResponse(fh.read(), content_type="application/octet-stream")
                response["Content-Disposition"] = "attachment; filename=" + os.path.basename(file_path)
                response["x-filename"] = file.name
                response["Access-Control-Expose-Headers"] = "x-filename"
                return response
        raise NotFound(status="file_doesnt_exists")

    match request.method:
        case "POST":
            return _post(request, uid, *args, **kwargs)
        case "GET":
            return _get(request, uid, *args, **kwargs)
