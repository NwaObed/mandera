"""Transform raw products: clean into the audit zone, then publish to staging."""

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

_COLUMNS = ["product_id", "product_name", "category", "price", "batch_id", "created_at"]


def transform(engine):
    """
    Read raw products, deduplicate and clean them, and write the result to
    the staging_tmp audit zone. Publishing to staging happens in write().
    """
    df = read_table(engine, RAW_TABLES["products"])

    if df.empty:
        print("  ⊘ No products to transform")
        return

    # Deduplicate
    df = df.drop_duplicates(subset=["product_id"], keep="last")

    # Null handling
    df = df.dropna(subset=["product_id", "product_name"])
    df["category"] = df["category"].fillna("Uncategorized")
    df["price"] = pd.to_numeric(df["price"], errors="coerce")

    # Reject invalid product pricing
    df = df[df["price"].gt(0) & (df["price"] < 100000)]
    df["price"] = df["price"].fillna(0)

    # Standardize
    df["product_name"] = df["product_name"].str.strip().str.title()
    df["category"] = df["category"].str.strip().str.title()
    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")

    replace_table(engine, STAGING_TMP_TABLES["products"], df, _COLUMNS)

    print(f"  ✓ Cleaned {len(df)} products → staging_tmp (audit zone)")


def write(engine):
    """
    Publish validated products from staging_tmp into staging via an
    idempotent PK upsert, then clear the audit table.
    """
    promote = text(f"""
        INSERT INTO {STAGING_TABLES['products']}
            (product_id, product_name, category, price, batch_id, created_at)
        SELECT product_id, product_name, category, price, batch_id, created_at::timestamp
        FROM {STAGING_TMP_TABLES['products']}
        ON CONFLICT (product_id) DO UPDATE SET
            product_name = EXCLUDED.product_name,
            category = EXCLUDED.category,
            price = EXCLUDED.price,
            batch_id = EXCLUDED.batch_id,
            created_at = EXCLUDED.created_at
    """)
    with engine.begin() as conn:
        result = conn.execute(promote)
        conn.execute(text(f"TRUNCATE {STAGING_TMP_TABLES['products']}"))

    print(f"  ✓ Published {result.rowcount} products → staging")


if __name__ == "__main__":
    eng = create_engine(POSTGRES_URL)
    transform(eng)
    write(eng)