"""
PostgreSQL configuration and table-name mappings.

Importing this module requires the Postgres env vars to be set —
which is correct, because only jobs that actually talk to Postgres
(extraction, transformation, validation, maintenance) import it.
"""

import os

from config import env  # noqa: F401  (loads .env once, for its side effect)

_REQUIRED = ["POSTGRES_HOST", "POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD"]
_missing = [name for name in _REQUIRED if not os.getenv(name)]
if _missing:
    raise EnvironmentError(f"Missing Postgres env vars: {', '.join(_missing)}. Set them in .env")

POSTGRES_CONFIG = {
    "host": os.getenv("POSTGRES_HOST"),
    "port": int(os.getenv("POSTGRES_PORT", "5432")),
    "database": os.getenv("POSTGRES_DB"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
}

POSTGRES_URL = (
    f"postgresql://{POSTGRES_CONFIG['user']}:{POSTGRES_CONFIG['password']}"
    f"@{POSTGRES_CONFIG['host']}:{POSTGRES_CONFIG['port']}"
    f"/{POSTGRES_CONFIG['database']}"
)

RAW_TABLES = {
    "customers": "raw.customers_raw",
    "products": "raw.products_raw",
    "orders": "raw.orders_raw",
}

STAGING_TABLES = {
    "customers": "staging.customers_clean",
    "products": "staging.products_clean",
    "orders": "staging.orders_clean",
}

# Audit zone for the Write-Audit-Publish flow: transforms write cleaned
# data here, validation runs against it, and only validated rows are
# promoted into STAGING_TABLES. Lets a bad transform fail validation
# without ever touching the published staging tables.
STAGING_TMP_TABLES = {
    "customers": "staging_tmp.customers_clean",
    "products": "staging_tmp.products_clean",
    "orders": "staging_tmp.orders_clean",
}