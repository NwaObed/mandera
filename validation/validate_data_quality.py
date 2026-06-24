"""
Data quality contract validation.

Runs AFTER the transforms but BEFORE the write/publish step, against the
cleaned data sitting in the staging_tmp audit zone. Raw data is allowed to
be messy but the transforms exist to clean it, so this gate asserts that
the cleaned OUTPUT satisfies the contract. Because it runs before publish,
a failure here keeps bad data out of the published staging tables entirely
(rather than only blocking the truncate of raw). A failure means a
transform let bad data through (a real bug), not merely a dirty source.

Checks:
  - order_id cannot be null
  - customer_id cannot be null on orders
  - product_id cannot be null on orders
  - amount must be positive
  - payment_status must match allowed values
  - batch_id must exist (source metadata)
"""

import psycopg2

from config.postgres_settings import POSTGRES_CONFIG
from config.settings import PAYMENT_STATUSES


class ValidationError(Exception):
    """Raised when data quality checks fail."""
    pass


def validate():
    """
    Run all quality checks against the cleaned data in the staging_tmp
    audit zone. Raises ValidationError if any check fails.
    """
    conn = psycopg2.connect(**POSTGRES_CONFIG)
    errors = []

    try:
        with conn.cursor() as cur:
            # ── order_id cannot be null ─────────────────────────
            cur.execute(
                "SELECT COUNT(*) FROM staging_tmp.orders_clean WHERE order_id IS NULL OR order_id = ''"
            )
            count = cur.fetchone()[0]
            if count > 0:
                errors.append(f"Found {count} orders with null order_id")

            # ── customer_id cannot be null on orders ───────────
            cur.execute(
                "SELECT COUNT(*) FROM staging_tmp.orders_clean WHERE customer_id IS NULL OR customer_id = ''"
            )
            count = cur.fetchone()[0]
            if count > 0:
                errors.append(f"Found {count} orders with null customer_id")

            # ── product_id cannot be null on orders ────────────
            cur.execute(
                "SELECT COUNT(*) FROM staging_tmp.orders_clean WHERE product_id IS NULL OR product_id = ''"
            )
            count = cur.fetchone()[0]
            if count > 0:
                errors.append(f"Found {count} orders with null product_id")

            # ── amount must be positive and not NaN ──────────────
            cur.execute(
                "SELECT COUNT(*) FROM staging_tmp.orders_clean WHERE amount <= 0"
            )
            count = cur.fetchone()[0]
            if count > 0:
                errors.append(f"Found {count} orders with invalid amount")

            # ── payment_status must be valid ───────────────────
            allowed = tuple(PAYMENT_STATUSES)
            cur.execute(
                "SELECT DISTINCT payment_status FROM staging_tmp.orders_clean WHERE payment_status NOT IN %s",
                (allowed,),
            )
            invalid = [row[0] for row in cur.fetchall()]
            if invalid:
                errors.append(f"Invalid payment_status values: {invalid}")

            # ── batch_id must exist ────────────────────────────
            cur.execute(
                "SELECT COUNT(*) FROM staging_tmp.orders_clean WHERE batch_id IS NULL OR batch_id = ''"
            )
            count = cur.fetchone()[0]
            if count > 0:
                errors.append(f"Found {count} orders with missing batch_id")

            # ── customers must have valid IDs, names, and emails ─
            cur.execute(
                "SELECT COUNT(*) FROM staging_tmp.customers_clean WHERE customer_id IS NULL OR customer_id = '' OR name IS NULL OR name = ''"
            )
            count = cur.fetchone()[0]
            if count > 0:
                errors.append(f"Found {count} customers with missing customer_id or name")

            cur.execute(
                "SELECT COUNT(*) FROM staging_tmp.customers_clean WHERE email IS NOT NULL AND email <> '' AND (email NOT LIKE '%@%.%' OR email LIKE '%@%@%' OR email LIKE '% @%' OR email LIKE '%@.%' OR email LIKE '%.@%')"
            )
            count = cur.fetchone()[0]
            if count > 0:
                errors.append(f"Found {count} customers with invalid email format")

            cur.execute(
                "SELECT COUNT(*) FROM staging_tmp.customers_clean WHERE city IS NULL OR city = ''"
            )
            count = cur.fetchone()[0]
            if count > 0:
                errors.append(f"Found {count} customers with missing city")

            # ── products must have valid IDs, names, and prices ───
            cur.execute(
                "SELECT COUNT(*) FROM staging_tmp.products_clean WHERE product_id IS NULL OR product_id = '' OR product_name IS NULL OR product_name = ''"
            )
            count = cur.fetchone()[0]
            if count > 0:
                errors.append(f"Found {count} products with missing product_id or product_name")

            cur.execute(
                "SELECT COUNT(*) FROM staging_tmp.products_clean WHERE price IS NULL OR price <= 0 OR price >= 100000"
            )
            count = cur.fetchone()[0]
            if count > 0:
                errors.append(f"Found {count} products with invalid price")

            cur.execute(
                "SELECT COUNT(*) FROM staging_tmp.products_clean WHERE batch_id IS NULL OR batch_id = ''"
            )
            count = cur.fetchone()[0]
            if count > 0:
                errors.append(f"Found {count} products with missing batch_id")

    finally:
        conn.close()

    if errors:
        error_msg = "Data validation failed:\n" + "\n".join(f"  ✗ {e}" for e in errors)
        print(error_msg)
        raise ValidationError(error_msg)

    print("  ✓ All validation checks passed")


if __name__ == "__main__":
    validate()