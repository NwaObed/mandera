"""Transform raw orders: clean into the audit zone, then publish to staging."""

from pathlib import Path
import sys

project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

import pandas as pd
from sqlalchemy import create_engine, text

from config.postgres_settings import (
    POSTGRES_URL,
    RAW_TABLES,
    STAGING_TABLES,
    STAGING_TMP_TABLES,
)
from transformation._db_io import read_table, replace_table

_COLUMNS = [
    "order_id", 
    "customer_id", 
    "product_id", 
    "region",
    "amount", 
    "quantity",
    "payment_status", 
    "batch_id", 
    "created_at",
]


def transform(engine):
    """
    Read raw orders, deduplicate and clean them, and write the result to
    the staging_tmp audit zone. Publishing to staging happens in write().
    """
    df = read_table(engine, RAW_TABLES["orders"])

    if df.empty:
        print("  ⊘ No orders to transform")
        return

    # Deduplicate on order_id
    df = df.drop_duplicates(subset=["order_id"], keep="last")

    # Null handling
    df = df.dropna(subset=["order_id", "customer_id", "product_id"])
    df = df[df["customer_id"].astype(str).str.strip() != ""]
    df = df[df["product_id"].astype(str).str.strip() != ""]

    # Type corrections
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")

    # Reject invalid amounts
    df = df[df["amount"].gt(0)]

    # Standardize
    df["region"] = df["region"].str.strip().str.title()
    df["payment_status"] = df["payment_status"].str.strip().str.lower()

    # Filter invalid payment statuses
    valid_statuses = {"paid", "failed", "pending"}
    df = df[df["payment_status"].isin(valid_statuses)]

    replace_table(engine, STAGING_TMP_TABLES["orders"], df, _COLUMNS)

    print(f"  ✓ Cleaned {len(df)} orders → staging_tmp (audit zone)")


def write(engine):
    """
    Publish validated orders from staging_tmp into staging via an
    idempotent PK upsert, then clear the audit table.
    """
    promote = text(f"""
        INSERT INTO {STAGING_TABLES['orders']}
            (order_id, customer_id, product_id, region, amount, quantity, payment_status, batch_id, created_at)
        SELECT order_id, customer_id, product_id, region, amount, quantity, payment_status, batch_id, created_at::timestamp
        FROM {STAGING_TMP_TABLES['orders']}
        ON CONFLICT (order_id) DO UPDATE SET
            customer_id = EXCLUDED.customer_id,
            product_id = EXCLUDED.product_id,
            region = EXCLUDED.region,
            amount = EXCLUDED.amount,
            payment_status = EXCLUDED.payment_status,
            batch_id = EXCLUDED.batch_id,
            created_at = EXCLUDED.created_at
    """)
    with engine.begin() as conn:
        result = conn.execute(promote)
        conn.execute(text(f"TRUNCATE {STAGING_TMP_TABLES['orders']}"))

    print(f"  ✓ Published {result.rowcount} orders → staging")


if __name__ == "__main__":
    eng = create_engine(POSTGRES_URL)
    transform(eng)
    write(eng)