"""
Extracts all records from MongoDB and writes them as JSON
to MinIO under date-partitioned paths (YYYY/MM/DD/).

MinIO serves as the durable archive — if anything fails downstream,
you can always replay from here.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
import sys

import boto3
from pymongo import MongoClient

project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from config.mongo_settings import MONGO_URI, MONGO_DB, MONGO_COLLECTIONS
from config.minio_settings import (
    MINIO_ENDPOINT,
    MINIO_ACCESS_KEY,
    MINIO_SECRET_KEY,
    MINIO_BUCKET,
    month_partition,
)


def _get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY,
        region_name="us-east-1",
    )


def _ensure_bucket(s3):
    try:
        s3.head_bucket(Bucket=MINIO_BUCKET)
    except s3.exceptions.ClientError:
        s3.create_bucket(Bucket=MINIO_BUCKET)
        print(f"  ✓ Created bucket: {MINIO_BUCKET}")


def _serialize_doc(doc: dict) -> dict:
    """Remove MongoDB _id and convert datetimes to ISO strings."""
    doc.pop("_id", None)
    for key, value in doc.items():
        if isinstance(value, datetime):
            doc[key] = value.isoformat()
    return doc


def extract_to_minio() -> dict:
    """
    Pull all docs from MongoDB and write to MinIO.
    Returns row counts per collection.
    """
    client = MongoClient(MONGO_URI)
    db = client[MONGO_DB]
    s3 = _get_s3_client()
    _ensure_bucket(s3)

    partition = month_partition()
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    counts = {}

    try:
        for name, collection_name in MONGO_COLLECTIONS.items():
            docs = list(db[collection_name].find())
            docs = [_serialize_doc(d) for d in docs]

            if docs:
                key = f"{name}/{partition}{run_id}.json"
                body = json.dumps(docs, indent=2, default=str)
                s3.put_object(
                    Bucket=MINIO_BUCKET,
                    Key=key,
                    Body=body.encode("utf-8"),
                    ContentType="application/json",
                )
                print(f"  ✓ Wrote {len(docs)} {name} to MinIO → {key}")

            counts[name] = len(docs)
    finally:
        client.close()

    return counts


if __name__ == "__main__":
    extract_to_minio()