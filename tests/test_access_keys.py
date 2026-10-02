# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""The access path: with django_access installed the erase key is an access token (``verify_api_key``).

Legacy keys reach it only through the import (``make_api_key``); the legacy table is never read on this path.
No customer carries the erase email, so a key that passes answers 404 "Customer account not found" — distinct
from the 401 of a refused key and from the 404 of an unknown channel.
"""

import secrets
from datetime import timedelta
from unittest.mock import patch

import pytest

pytest.importorskip("django_access")

from django.contrib import admin  # noqa: E402
from django.core.management import CommandError, call_command  # noqa: E402
from django.utils import timezone  # noqa: E402
from django_access.models import ApiToken, Application  # noqa: E402
from django_access.services.access_service import Actor  # noqa: E402
from django_access.services.tokens import hash_key, issue_token, revoke_token, set_token_expiry  # noqa: E402

from django_accounts.models import APIAdminKey  # noqa: E402
from django_accounts.utils.api_keys import ERASE_SCOPE  # noqa: E402

CHANNEL, SECOND = "test-channel", "second-channel"
API_KEY, ADMIN_KEY = "HTTP_X_API_KEY", "HTTP_X_API_ADMIN_KEY"
SYSTEM = Actor()


@pytest.fixture
def erase(api_client):
    def erase(key: str, channel_idx: str = CHANNEL, header: str = ADMIN_KEY):
        url = f"/api-admin/accounts/1/{channel_idx}/customer/delete"
        return api_client.delete(url, {"email": "nobody@example.com"}, format="json", **{header: key})

    return erase


def _passed(response) -> bool:
    return response.status_code == 404 and response.json()["meta"]["message"] == "Customer account not found"


def _refused(response) -> bool:
    return response.status_code == 401 and response.json()["data"] == "Invalid api admin key"


@pytest.fixture
def issue(db):
    """Issue a token of one scope; a secret scope gets the expiry it must carry."""
    application = Application.objects.create(name="accounts-tests")

    def issue(scope: str = ERASE_SCOPE, channel_idx: str | None = None) -> tuple[ApiToken, str]:
        expiry = timezone.now() + timedelta(days=30)
        return issue_token(application, scopes=[scope], channel_idx=channel_idx, expires_at=expiry, actor=SYSTEM)

    return issue


def _later(days: int):
    return patch("django.utils.timezone.now", return_value=timezone.now() + timedelta(days=days))


@pytest.mark.django_db
class TestTokenLifecycle:
    def test_revoked_token_is_refused(self, channel, issue, erase):
        token, raw = issue(channel_idx=CHANNEL)
        assert _passed(erase(raw))
        revoke_token(token, actor=SYSTEM)
        assert _refused(erase(raw))

    def test_legacy_token_without_expiry_keeps_working(self, channel, make_api_key, erase):
        raw = make_api_key(channel=channel)
        token = ApiToken.objects.get(key_hash=hash_key(raw))
        assert (token.legacy, token.expires_at) == (True, None)
        assert _passed(erase(raw))
        with _later(days=3650):
            assert _passed(erase(raw))

    def test_legacy_token_past_its_team_expiry_is_refused(self, channel, make_api_key, erase):
        raw = make_api_key(channel=channel)
        token = ApiToken.objects.get(key_hash=hash_key(raw))
        set_token_expiry(token, expires_at=timezone.now() + timedelta(days=1), actor=SYSTEM)
        assert _passed(erase(raw))
        with _later(days=2):
            assert _refused(erase(raw))

    def test_key_only_in_the_legacy_table_is_refused(self, channel, erase):
        raw = secrets.token_hex(32)
        APIAdminKey.objects.create(channel=channel, key=raw)
        assert _refused(erase(raw))


@pytest.mark.django_db
class TestScopeAndChannel:
    def test_token_of_another_channel_is_refused(self, channel, second_channel, issue, erase):
        _, raw = issue(channel_idx=SECOND)
        assert _refused(erase(raw))

    def test_unpinned_token_works_on_any_channel(self, channel, second_channel, issue, erase):
        _, raw = issue()
        assert _passed(erase(raw, CHANNEL))
        assert _passed(erase(raw, SECOND))

    @pytest.mark.parametrize("scope", ["checkout.erase", "checkout.storefront"])
    def test_checkout_token_is_refused(self, scope, channel, issue, erase):
        _, raw = issue(scope, CHANNEL)
        assert _refused(erase(raw))

    def test_erase_token_in_x_api_key_is_refused(self, channel, issue, erase):
        _, raw = issue(channel_idx=CHANNEL)
        assert _refused(erase(raw, header=API_KEY))

    def test_unknown_channel_is_404_before_the_key(self, channel, issue, erase):
        _, raw = issue()
        response = erase(raw, "no-such-channel")
        assert response.status_code == 404
        assert response.json()["data"] == "Channel does not exist"


@pytest.mark.django_db
def test_every_failure_gives_one_response(channel, second_channel, issue, erase):
    expired, expired_raw = issue(channel_idx=CHANNEL)
    ApiToken.objects.filter(pk=expired.pk).update(expires_at=timezone.now() - timedelta(minutes=1))
    revoked, revoked_raw = issue(channel_idx=CHANNEL)
    revoke_token(revoked, actor=SYSTEM)
    keys = {
        "unknown": "ent_api_" + secrets.token_urlsafe(32),
        "expired": expired_raw,
        "revoked": revoked_raw,
        "wrong scope": issue("checkout.erase", CHANNEL)[1],
        "wrong channel": issue(channel_idx=SECOND)[1],
    }
    responses = {kind: erase(raw) for kind, raw in keys.items()}
    outcomes = {kind: (response.status_code, response.content) for kind, response in responses.items()}
    assert len(set(outcomes.values())) == 1, outcomes
    assert outcomes["unknown"][0] == 401


@pytest.mark.django_db
def test_admin_pages_never_show_the_raw_key(channel, admin_user, rf, settings):
    settings.ROOT_URLCONF = "tests.admin_urls"
    key = APIAdminKey.objects.create(channel=channel)
    model_admin = admin.site.get_model_admin(APIAdminKey)
    request = rf.get("/")
    request.user = admin_user
    assert not model_admin.has_add_permission(request)
    assert not model_admin.has_change_permission(request, key)
    for response in (model_admin.changelist_view(request), model_admin.change_view(request, str(key.pk))):
        html = response.render().content.decode()
        assert response.status_code == 200
        assert key.key not in html
        assert f"…{key.key[-4:]}" in html


@pytest.mark.django_db
def test_key_command_refuses_and_names_the_token_command(channel):
    with pytest.raises(CommandError, match=f"access_token create --scope {ERASE_SCOPE} --channel {CHANNEL}"):
        call_command("generate-api-admin-key", CHANNEL)
    assert not APIAdminKey.objects.exists()
