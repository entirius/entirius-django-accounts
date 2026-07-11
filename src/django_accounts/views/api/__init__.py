from .address_book import (
    customer_addresses,
    customer_addresses_defaults,
    customer_addresses_files,
)
from .customer import (
    account_create,
    customer_change_password,
    customer_create_confirm,
    customer_delete,
    customer_me,
    customer_profile,
    customer_reset_password,
    customer_reset_password_confirm,
)
from .social_login import callback_via_provider, login_via_provider, return_client_token
from .token import token_blacklist, token_create, token_refresh, token_validate
from .wishlist import wishlist_detail, wishlist_product
