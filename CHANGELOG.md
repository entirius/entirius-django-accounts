# Changelog

## Unreleased

- `customer/tokens/` answers 403 `user_not_customer` instead of 500 when the login is valid but the
  user has no Customer profile (e.g. a staff-only account).
- Docs: `JWTAccessBackend` in `AUTHENTICATION_BACKENDS` is required for the customer endpoints.

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
