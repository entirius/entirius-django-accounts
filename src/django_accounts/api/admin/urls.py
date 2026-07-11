# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from django.urls import path

from django_accounts.api.admin.views import ChannelViewSet, CustomerViewSet, GroupViewSet

urlpatterns = [
    path("customers/", CustomerViewSet.as_view({"get": "list"}), name="accounts-admin-customer-list"),
    path("customers/<str:uid>/", CustomerViewSet.as_view({"get": "retrieve"}), name="accounts-admin-customer-detail"),
    path("groups/", GroupViewSet.as_view({"get": "list"}), name="accounts-admin-group-list"),
    path("channels/", ChannelViewSet.as_view({"get": "list"}), name="accounts-admin-channel-list"),
]
