# django-accounts

Customer authentication and account management module for the Volkanos ecommerce platform —
registration with double opt-in, JWT login (simplejwt), address book with file attachments,
per-channel wishlist, social login (Google/Facebook) and CSV import/export.
v1 public API (function-based views + marshmallow DTOs), v2 read-only admin API
(Pydantic + drf-spectacular).

## Installation

```shell
pip install entirius-django-accounts
```

Add the app to your project:

```python
INSTALLED_APPS = [
    ...
    "django_accounts",
]
```

Two settings are required at import time: `PRIVATE_DIR` (private file storage root) and
`MIGRATION_0023_MECHANISM` (wishlist restructuring mode; use `1` on fresh installations).

Register the JWT backend, or every customer endpoint behind `@authenticate` (`customer/me/`,
profile, addresses, wishlist, password change, logout) answers 401 even with a valid token:

```python
AUTHENTICATION_BACKENDS = [
    "django_accounts.backends.JWTAccessBackend",
    "django.contrib.auth.backends.ModelBackend",  # Django admin login
]
```

Optional PIM integration (product-representation sync worker):

```shell
pip install "entirius-django-accounts[pim]"
```

## Development

```shell
make install     # sync dependencies (uv)
make check       # lint + format check (ruff)
make test        # test suite (pytest + pytest-django, postgres via DATABASE_URL)
```

Architecture, API and model reference: [AGENTS.md](AGENTS.md).

## License

Mozilla Public License 2.0 — see [LICENSE](LICENSE).
