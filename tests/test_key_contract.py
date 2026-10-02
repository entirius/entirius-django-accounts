# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Characterization of today's accounts key contract (X-API-ADMIN-KEY on ``customer/delete``).

Pins what the keyed route answers — quirks included — so moving the key check onto another key store cannot
change a status or a body. Keys come only from the ``make_api_key`` helper.
"""

import secrets

import pytest

from django_accounts.models import Customer

ERASE_EMAIL = "testuser@example.com"


def _delete_url(channel_idx: str) -> str:
    return f"/api-admin/accounts/1/{channel_idx}/customer/delete"


def _delete(api_client, key: str | None, channel_idx: str = "test-channel"):
    headers = {} if key is None else {"HTTP_X_API_ADMIN_KEY": key}
    return api_client.delete(_delete_url(channel_idx), {"email": ERASE_EMAIL}, format="json", **headers)


def _refusal(response) -> tuple[int, str, str]:
    """The v1 envelope puts the refusal text in ``data``, not in ``meta.message`` (quirk: positional arg)."""
    body = response.json()
    return response.status_code, body["meta"]["status"], body["data"]


@pytest.fixture(autouse=True)
def _live_key(channel, make_api_key):
    """Valid keys exist in every test, so a refusal proves the lookup, not an empty key store."""
    make_api_key(channel=channel)


@pytest.mark.django_db
class TestAdminKeyCustomerDelete:
    def test_unknown_channel_is_404_before_the_key(self, api_client, channel, make_api_key):
        response = _delete(api_client, make_api_key(channel=channel), channel_idx="no-such-channel")
        assert response.status_code == 404

    def test_missing_key_is_401(self, api_client, channel):
        assert _refusal(_delete(api_client, None)) == (401, "UNAUTHORIZED", "Invalid api admin key")

    def test_wrong_key_is_401(self, api_client, channel):
        assert _refusal(_delete(api_client, secrets.token_hex(32))) == (401, "UNAUTHORIZED", "Invalid api admin key")

    def test_other_channel_key_is_refused_like_a_wrong_key(self, api_client, channel, second_channel, make_api_key):
        wrong = _delete(api_client, secrets.token_hex(32))
        foreign_key = make_api_key(channel=second_channel)
        foreign = _delete(api_client, foreign_key)
        assert _refusal(foreign) == _refusal(wrong)
        assert foreign_key not in foreign.content.decode()

    def test_key_without_channel_is_refused(self, api_client, channel, make_api_key):
        assert _delete(api_client, make_api_key(channel=None)).status_code == 401

    def test_key_in_x_api_key_header_is_refused(self, api_client, channel, make_api_key):
        response = api_client.delete(
            _delete_url(channel.idx), {"email": ERASE_EMAIL}, format="json", HTTP_X_API_KEY=make_api_key(channel)
        )
        assert response.status_code == 401

    def test_right_key_deletes_the_customer(self, api_client, channel, customer, make_api_key):
        response = _delete(api_client, make_api_key(channel=channel))
        assert response.status_code == 200
        assert response.json()["data"] == {"deleted": True, "uid_ok": [str(customer.uid)]}
        assert not Customer.objects.filter(pk=customer.pk).exists()


@pytest.mark.django_db
def test_public_token_validate_answers_without_a_key(api_client, channel):
    response = api_client.post(
        f"/api/accounts/1/{channel.idx}/customer/tokens/validate/", {"access": "not-a-token"}, format="json"
    )
    assert response.status_code == 200
    assert response.json()["data"]["is_valid"] is False
