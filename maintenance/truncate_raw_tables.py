"""
Truncates all raw landing tables after successful transformation.

Reads and executes sql/truncate_raw_tables.sql so the SQL
lives in one place.
"""

import os

import psycopg2

from config.postgres_settings import POSTGRES_CONFIG

SQL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "sql",
    "truncate_raw_tables.sql",
)


def truncate():
    """Execute the truncate SQL against all raw tables."""
    with open(SQL_PATH) as f:
        sql = f.read()

    conn = psycopg2.connect(**POSTGRES_CONFIG)
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
        print("  ✓ Truncated raw.customers_raw")
        print("  ✓ Truncated raw.products_raw")
        print("  ✓ Truncated raw.orders_raw")
    finally:
        conn.close()


if __name__ == "__main__":
    truncate()