# Changelog

## Unreleased

- Keys verified by django-access when installed: the X-API-ADMIN-KEY erase route checks access tokens
  through `verify_api_key` (scope `accounts.erase`), never the legacy table. Without django-access
  nothing changes. `generate-api-admin-key` then refuses and names `access_token create`; the key admin
  becomes read-only.
- Without django-access the key admin shows a new key once on creation; with it, delete is blocked too.
- The key admin shows only the last four characters of a key.

## 5.0.1 — 2026-07-13

- Fix broken format string in the password validator help text.

## 5.0.0 — 2026-07-11

- Initial public release: the customer identity layer — registration with double
  opt-in, JWT authentication, password policy, social login (Google/Facebook),
  address book, channel-scoped wishlists, GDPR consent management, and
  channel-scoped admin API keys.
- Read-only admin API v2: customers list/detail, groups, channels — Pydantic
  response schemas with OpenAPI docs.
- Migrations squashed into a single initial migration for the Entirius epoch.
