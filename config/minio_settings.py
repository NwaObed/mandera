"""
MinIO (S3-compatible object storage) configuration.

Imported only by jobs that write to / read from object storage.
"""

import os
from datetime import datetime, timezone

from config import env  # noqa: F401  (loads .env once, for its side effect)

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")
MINIO_ACCESS_KEY = os.getenv("MINIO_ROOT_USER")
MINIO_SECRET_KEY = os.getenv("MINIO_ROOT_PASSWORD")
MINIO_BUCKET = os.getenv("MINIO_BUCKET")


def month_partition() -> str:
    """Returns month as a MinIO partition path: YYYY/MM/"""
    now = datetime.now(timezone.utc)
    return now.strftime("%Y/%m/")