# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from django.urls import include, path

from . import settings
from .views import admin, api

paths = [
    path("customer/tokens/", api.token_create, name="token-create"),
    path("customer/tokens/refresh/", api.token_refresh, name="token-refresh"),
    path("customer/tokens/blacklist/", api.token_blacklist, name="token-blacklist"),
    path("customer/tokens/validate/", api.token_validate, name="token-validate"),
    path("customer/signup/", api.account_create, name="signup"),
    path("customer/signup/<str:uid>/", api.customer_create_confirm, name="signup-confirm"),
    path("customer/password/reset/", api.customer_reset_password, name="password-reset"),
    path("customer/password/reset/<str:key>/", api.customer_reset_password_confirm, name="password-reset-confirm"),
    path("customer/password/change/", api.customer_change_password, name="password-change"),
    path("customer/me/", api.customer_me, name="me"),
    path("customer/<str:uid>/profile/", api.customer_profile, name="profile"),
    path("customer/<str:uid>/delete/", api.customer_delete, name="customer-delete"),
    path("customer/login/<str:provider_name>/", api.login_via_provider, name="signup"),
    path("customer/login/<str:provider_name>/callback/", api.callback_via_provider, name="signup"),
    path("customer/tokenize/", api.return_client_token, name="signup"),
    path("wishlist/product/", api.wishlist_product, name="wishlist_product"),
    path("wishlist/", api.wishlist_detail, name="wishlist"),
    path("customer/<str:uid>/addresses/", api.customer_addresses, name="addresses"),
    path("customer/<str:uid>/addresses/defaults/", api.customer_addresses_defaults, name="addresses-defaults"),
    path("customer/<str:uid>/addresses/files/", api.customer_addresses_files, name="addresses-files"),
]

admin_paths = [path("customer/delete", admin.admin_customer_delete, name="accounts-admin-customer-delete")]

urlpatterns = [
    path("api/accounts/v2/admin/", include("django_accounts.api.admin.urls")),  # v2 admin — BEFORE v1
    path(f"{settings.PUBLIC_BASE_URL}/accounts/<str:version>/<str:channel_idx>/", include(paths)),
    path(f"{settings.ADMIN_BASE_URL}/accounts/<str:version>/<str:channel_idx>/", include(admin_paths)),
]
