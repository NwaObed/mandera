"""Transform raw customers: clean into the audit zone, then publish to staging."""

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
    "customer_id",
    "name",
    "email",
    "phone",
    "city",
    "address",
    "country",
    "batch_id",
    "created_at"
]

def transform_customers(engine):

    "Read raw customers, dedup and clean, and write the results to staging_tmp audit zone. Does not touch published staging - that only happens in the write() after validation."

    df = read_table(engine, RAW_TABLES["customers"])

    if df.empty:
        print("  ⊘ No customers to transform")
        return

    print(f"  ✓ Read {len(df)} customers from raw")

    # Deduplicate on customer_id
    df = df.drop_duplicates(subset=["customer_id"], keep="last")

    # Null handling
    df = df.dropna(subset=["customer_id", "name"])
    df["email"] = df["email"].fillna("").astype(str).str.strip().str.lower()
    df["email"] = df["email"].where(
        df["email"].str.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$"),
        "unknown@example.com",
    )
    df["email"] = df["email"].replace({"invalid-email": "unknown@example.com"})
    df["phone"] = df["phone"].fillna("N/A")
    df["phone"] = df["phone"].replace({"12345": "000-000-0000"})
    df["address"] = df["address"].fillna("").astype(str).str.strip()
    df["address"] = df["address"].replace({"": "Unknown"})
    df["country"] = df["country"].fillna("Unknown")

    # Standardize
    df["name"] = df["name"].str.strip().str.title()
    df["city"] = df["city"].str.title()
    df["email"] = df["email"].str.strip().str.lower()
    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")

    replace_table(engine, STAGING_TMP_TABLES["customers"], df, _COLUMNS)

    print(f"  ✓ Cleaned {len(df)} customers → staging_tmp (audit zone)")


def write(engine):
    """
    Publish validated customers from staging_tmp into staging via an
    idempotent PK upsert, then clear the audit table.
    """
    promote = text(f"""
        INSERT INTO {STAGING_TABLES['customers']}
            (customer_id, name, email, phone, city, address, country, batch_id, created_at)
        SELECT customer_id, name, email, phone, city, address, country, batch_id, created_at::timestamp
        FROM {STAGING_TMP_TABLES['customers']}
        ON CONFLICT (customer_id) DO UPDATE SET
            name = EXCLUDED.name,
            email = EXCLUDED.email,
            phone = EXCLUDED.phone,
            city = EXCLUDED.city,
            address = EXCLUDED.address,
            country = EXCLUDED.country,
            batch_id = EXCLUDED.batch_id,
            created_at = EXCLUDED.created_at
    """)
    with engine.begin() as conn:
        result = conn.execute(promote)
        conn.execute(text(f"TRUNCATE {STAGING_TMP_TABLES['customers']}")) # Clear the audit table after publishing

    print(f"  ✓ Published {result.rowcount} customers → staging")


if __name__ == "__main__":
    eng = create_engine(POSTGRES_URL)
    transform_customers(eng)
    write(eng)