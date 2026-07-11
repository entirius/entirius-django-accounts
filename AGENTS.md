# AGENTS.md

Customer authentication and account management module for the Volkanos ecommerce platform — distribution
`entirius-django-accounts`, Django app `django_accounts`. Handles registration, JWT login, address book,
wishlist, social login (Google/Facebook), and CSV import/export.

## Commands

| Command | Meaning |
|---|---|
| `make install` | sync dependencies (uv, incl. extras) |
| `make check` | lint + format-check (ruff) |
| `make fix` | auto-fix lint + format |
| `make test` | test suite (pytest + pytest-django) |

## Conventions

- English only: code, docs, commits, branches, PRs.
- MPL-2.0: every non-trivial source file carries the license header (pre-commit inserts it).
- Toolchain: uv + ruff + hatchling + pytest; all config in `pyproject.toml`; `uv.lock` committed.
- Git flow: `master` (production) + `develop` (integration); changes land via PR; semver tag on `master`.
- Never rename the package / Django app_label / DB table prefix `django_accounts` — it is a schema contract.
- Migrations are part of the public contract — never edit an already released migration.
- Default: do not commit — git is the user's call.

## Architecture

```
src/django_accounts/
├── models/                         # 12 ORM models + 1 proxy
│   ├── customer.py                 #   Customer (O2O → User), UserExtensionProxy
│   ├── address.py                  #   Address (FK → Customer), AddressManager
│   ├── channel.py                  #   Channel (idx, label, language FK)
│   ├── file.py                     #   File, AddressFile (both FK → Customer)
│   ├── group.py                    #   Group (customer segmentation)
│   ├── wishlist.py                 #   Wishlist, WishlistProduct (M2M through)
│   ├── product_representation.py   #   ProductRepresentation (SKU + name_t9n per channel)
│   ├── revoke.py                   #   Revoke (logout tracking)
│   ├── socials.py                  #   SocialLoginProviders (google/facebook config)
│   ├── apiadminkey.py              #   APIAdminKey (SHA256 generated, per channel)
│   └── managers.py                 #   WishlistManager (get_record, guest_wishlist_to_customer)
│
├── views/
│   ├── api/                        # Public v1 function-based views
│   │   ├── customer.py             #   signup, confirm, me, profile, delete, password
│   │   ├── token.py                #   create, refresh, blacklist, validate
│   │   ├── address_book.py         #   addresses CRUD + defaults + file upload
│   │   ├── wishlist.py             #   wishlist detail + product add/remove/extra
│   │   └── social_login.py         #   Google/Facebook OAuth2 login + callback + tokenize
│   └── admin/
│       └── customer.py             #   admin_customer_delete (by email, @admin_view)
│
├── api/                            # DRF v2 admin API (read-only)
│   └── admin/
│       ├── views.py                #   CustomerViewSet, GroupViewSet, ChannelViewSet
│       ├── urls.py                 #   4 endpoints under api/accounts/v2/admin/
│       └── pagination.py           #   AdminPageNumberPagination (20/page, max 100)
│
├── schemas/                        # Pydantic v2 response schemas (v2 admin API)
├── services/                       # CustomerService, admin query service, CSV import helpers
├── dto/                            # marshmallow-dataclass request/response objects (v1 API)
├── management/commands/            # 5 management commands (kebab-case filenames)
├── utils/                          # decorators (channel_view, admin_view), address helpers
├── backends.py                     # Custom auth backend
├── email_confirmation.py           # EmailChangePasswordHMAC (password reset HMAC)
├── password_validators.py          # CapitalSymbolAndNumbersValidator, SpaceValidator
├── jwt.py                          # TokenAccessSocialLogin (short-lived social token)
├── settings.py                     # ~25 module settings (see Settings Reference)
└── urls.py                         # URL routing (public + admin prefix from settings)
```

Layer rule: `Views → Services → Models → DB`. No ORM in views — use services or managers.

## API v1 Endpoints

Function-based views (v1 style: marshmallow DTO validation). URL prefix configured via
`API_PUBLIC_BASE_URL` and `API_ADMIN_BASE_URL` settings (defaults: `api`, `api-admin`).

```
{PUBLIC_BASE_URL}/accounts/<version>/<channel_idx>/
├── customer/tokens/                POST (create)          -- JWT login
├── customer/tokens/refresh/        POST                   -- refresh access token
├── customer/tokens/blacklist/      POST (auth)            -- logout / invalidate refresh
├── customer/tokens/validate/       POST                   -- validate access token
├── customer/signup/                POST                   -- register + double optin email
├── customer/signup/<uid>/          POST                   -- confirm email (key via querystring)
├── customer/password/reset/        POST                   -- send password reset email
├── customer/password/reset/<key>/  POST                   -- confirm reset with new password
├── customer/password/change/       POST (auth)            -- change password (old + new)
├── customer/me/                    GET (auth)             -- authenticated user info
├── customer/<uid>/profile/         GET, PATCH (auth)      -- customer profile
├── customer/<uid>/delete/          DELETE (auth)          -- self-delete + blacklist tokens
├── customer/login/<provider>/      GET                    -- social OAuth2 redirect
├── customer/login/<provider>/callback/ GET               -- social OAuth2 callback
├── customer/tokenize/              GET                    -- exchange access_social token
├── customer/<uid>/addresses/       GET, PUT, PATCH, DELETE (auth) -- address CRUD (?id=pk)
├── customer/<uid>/addresses/defaults/ GET, POST (auth)   -- get/set billing+shipping defaults
├── customer/<uid>/addresses/files/ GET, POST             -- upload / download address files
├── wishlist/                       GET, POST (auth/guest) -- wishlist detail + merge guest→customer
└── wishlist/product/               POST, DELETE, PATCH   -- add/remove/update extra on products

{ADMIN_BASE_URL}/accounts/<version>/<channel_idx>/
└── customer/delete                 DELETE (@admin_view)   -- admin delete customer by email
```

**Auth mechanisms (v1):**
- `@authenticate` + `@require_authentication` — simplejwt Bearer token
- `@admin_view` — `APIAdminKey` header authentication (admin endpoints)
- `@channel_view` — resolves `Channel` from URL `channel_idx` into `kwargs["channel"]`

### API v2 Admin (Read-Only)

URL prefix: `api/accounts/v2/admin/` — no channel scope (admin sees cross-channel data).
Auth: `JWTAuthentication` + `IsAdminUser`. Pydantic response schemas + drf-spectacular OpenAPI.

```
api/accounts/v2/admin/
├── customers/              GET    -- paginated list (search, group, channel, status filters, ordering)
├── customers/<uid>/        GET    -- full profile + addresses + session info + wishlist count
├── groups/                 GET    -- customer groups with customer counts
└── channels/               GET    -- accounts channels with default language
```

## Data Model

```
User (Django auth)
    └── Customer (O2O)               -- profile, is_active, is_verified, uid
         ├── source_channel: Channel  -- registration channel
         ├── blacklist_channels: [Channel]  -- M2M, no-login list
         ├── group: Group             -- customer segment
         ├── language: Language       -- from django_regional
         ├── billing_address: Address  (FK, nullable)
         ├── shipping_address: Address (FK, nullable)
         └── addresses: [Address]     -- all addresses (reverse FK)
              └── AddressFile          -- file attachments (FK → Address + Customer)
                    └── File           -- base file model (stored in PRIVATE_DIR/customer/{uid}/)

Channel
    ├── customers_source: [Customer]   -- reverse: customers registered here
    ├── customers_blacklist: [Customer] -- reverse: blocked customers
    ├── Wishlist                        -- per channel
    ├── ProductRepresentation           -- SKU name cache per channel
    ├── SocialLoginProviders            -- OAuth provider config per channel
    └── APIAdminKey                     -- admin API auth key per channel

Wishlist (uid, customer FK, channel FK)
    └── WishlistProduct (through table)
         └── ProductRepresentation (sku + name_t9n JSON)

Revoke (user FK, created_at)           -- tracks last logout time

UserExtensionProxy                     -- proxy on User, adds is_customer property
```

- `Customer.email` is a `@property` — queries allauth `EmailAddress` (primary + verified)
- `Customer.first_name` / `Customer.last_name` delegate to `user.first_name` / `user.last_name`
- `ProductRepresentation.name` falls back to `sku` if `name_t9n` is empty

## Key Enums

| Enum | Values |
|------|--------|
| **Sex** (Customer) | male, female, other (TextChoices) |
| **FileType** | default, address_attachment (TextChoices) |
| **AddressSourceEnum** | UNKNOWN(0), PWA(1), MAGENTO(2), EXTERNAL(3), CSV(4) |
| **SocialLoginProviders.provider** | google, facebook (hard-coded choices) |

## Unique Constraints

| Model | Field(s) | Type |
|-------|----------|------|
| Customer | `uid` | unique (UUID) |
| Channel | `idx` | unique |
| Channel | `label` | unique |
| Group | `code` | unique |
| Group | `name` | unique |
| ProductRepresentation | `(sku, channel)` | UniqueConstraint |
| Wishlist | `(customer, channel)` | UniqueConstraint |
| Address | check: `(firstname+lastname) OR company NOT NULL` | CheckConstraint |
| Address | check: `is_company → company+tax_id NOT NULL` | CheckConstraint |

## Settings Reference

Two settings raise `EnvironmentError` at import time if unset: `PRIVATE_DIR` and `MIGRATION_0023_MECHANISM`.

| Setting | Default | Description |
|---------|---------|-------------|
| `PRIVATE_DIR` | **required** | Root for private file storage |
| `MIGRATION_0023_MECHANISM` | **required** | Wishlist migration mode: 1=delete all, 2=multi-channel, 3=assign |
| `T9N_DEFAULT_LANG` | `"pl"` | Fallback language for name_t9n resolution |
| `EMAIL_DOUBLE_OPTIN` | `True` | Send confirmation email on signup |
| `ACCOUNTS_CUSTOMER_IS_ACTIVE_WITHOUT_DOUBLE_OPTIN` | `False` | Auto-activate when double optin off |
| `IS_ACTIVE_REQUIRED` | `True` | Block login if customer.is_active=False |
| `IS_VERIFY_REQUIRED` | `False` | Block login if customer.is_verified=False |
| `ACCOUNTS_PASSWORD_MIN_LENGTH` | `8` | Minimum password length |
| `ACCOUNTS_PASSWORD_MIN_CAPITAL_LETTERS` | `1` | Capital letters required |
| `ACCOUNTS_PASSWORD_MIN_SPECIAL_SYMBOLS` | `1` | Special symbols required |
| `ACCOUNTS_PASSWORD_MIN_NUMBERS` | `1` | Numbers required |
| `JWT_REFRESH_LIFETIME` | `3` | Refresh token lifetime in days |
| `JWT_SECRET` | hardcoded dev value | Override in production |
| `JWT_ALGORITHM` | `"HS256"` | JWT signing algorithm |
| `API_PUBLIC_BASE_URL` | `"api"` | Public URL prefix |
| `API_ADMIN_BASE_URL` | `"api-admin"` | Admin URL prefix |
| `NEW_ACCOUNT_REDIRECT_URL` | `None` | Email confirmation redirect URL |
| `RESET_PASSWORD_REDIRECT_URL` | `None` | Password reset redirect URL |
| `NEW_ADDRESS_SHOULD_BE_DEFAULT` | `False` | Auto-set new address as default |
| `BILLING_ADDRESS_EDITABLE` | auto | `False` if django_regon_api installed, else `True` |
| `BILLING_ADDRESS_PHONE_EDITABLE` | auto | `False` if django_regon_api installed, else `True` |
| `ADMIN_DELETE_CUSTOMER_MAX_BATCH` | `5` | Max customers per admin delete request |
| `WISHLIST_PRODUCT_PER_PAGE` | `30` | Wishlist pagination size |
| `ACCOUNTS_CHANNEL_BLACKLIST` | `{}` | `{channel_idx: [blacklisted_channel_idxs]}` applied on signup |
| `SPECIFY_KEYS_EXTRA_PROFILE_DATA_IN_API` | `None` | Whitelist keys from customer.extra in profile API |
| `MAGENTO2_URL_FOR_CHECKOUT_EXPORT` | `None` | Magento2 export endpoint |
| `MAGENTO2_TOKEN_FOR_CHECKOUT_EXPORT` | `None` | Magento2 export API token |

## Management Commands

| Command | Description |
|---------|-------------|
| `accounts-import-from-csv` | Import customer accounts from CSV file (`--file_path`, defaults to `IMPORT_DIR/accounts/accounts.csv`) |
| `addresses-import-from-csv` | Import customer addresses from CSV file |
| `fill-accounts-product-representation-from-pim` | Sync ProductRepresentation cache from PIM data (`--pim_shop_idx`; requires the `pim` extra) |
| `generate-api-admin-key` | Generate SHA256 APIAdminKey for a channel and save to file (`channel_idx`, `--file_path`) |
| `module-accounts-export-to-magento` | Export accounts to Magento2 (empty command stub) |

## Dependencies

**Runtime:** Django, DRF, simplejwt, django-allauth (email verification, EmailAddress model),
django-admin-inline-paginator (admin inlines), marshmallow + marshmallow-dataclass (v1 DTO validation),
pydantic + drf-spectacular (v2 admin API), PyJWT (social login short-lived token), requests, tqdm.

**Entirius modules:**
- `entirius-django-regional` — Language, Country models used in Customer FK fields
- `entirius-django-utils` — `api_view`, `authenticate`, `require_authentication`, `parse_body`, `channel_view` decorators
- `entirius-django-email` — `NewAccountEmail`, `ResetPasswordEmail` transactional email services
- `entirius-py-process-logger` — structured logging (`ProcessLogger`, `ProcessLoggerMixin`)
- `entirius-py-idx-normalizator`, `entirius-py-int-enum-choices` — helpers

**Optional:**
- `entirius-django-pim` (`pim` extra) — lazy import in the product-representation worker
- `django_regon_api` — when installed, auto-locks billing address fields

## Testing

Tests run on postgres via `DATABASE_URL` (CI provides a postgres service; locally point it at any postgres 15+).

```bash
make install
make test
```

## Gotchas

- `PRIVATE_DIR` and `MIGRATION_0023_MECHANISM` raise `EnvironmentError` at import if unset — set both before starting Django
- `T9N_DEFAULT_LANG` defaults to `"pl"` not `"en"` — affects `ProductRepresentation.name` and `name_lang()` fallback
- `Customer.email` is a `@property` querying allauth `EmailAddress` — always access via `customer.email.email`, not a plain field
- `UserExtensionProxy` is a proxy model on Django's User — excluded from ERD, exposes only `is_customer` property
- v1 views use marshmallow DTOs (legacy pattern). v2 admin API uses Pydantic + drf-spectacular
- `File` is stored in `FileSystemStorage` under `PRIVATE_DIR/customer/{uid}/` — not in STATIC/MEDIA, requires custom download view
- `AddressFile.save()` auto-sets `customer` from `address.customer` and overrides `file_type` to `ADDRESS_ATTACHMENT`
- Social login produces a short-lived `access_social` token — frontend exchanges it at `customer/tokenize/` for simplejwt tokens
- `django_accounts.Channel` is separate from `django_pim.Channel` — sync via `fill-accounts-product-representation-from-pim`
- One `Wishlist` per `(customer, channel)` — `MIGRATION_0023_MECHANISM` controls how pre-existing data was restructured

## Reference Docs

| File | Content |
|------|---------|
| `docs/erd-config.yaml` | ERD diagram config (two groups: customers-identity, wishlist-commerce) |
