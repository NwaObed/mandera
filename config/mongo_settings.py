"""
MongoDB Atlas configuration.

Importing this module only requires MongoDB env vars — it does NOT
touch Postgres or MinIO, so a job that only talks to Mongo never has
to provide unrelated credentials.
"""

import os

from config import env  # noqa: F401  (loads .env once, for its side effect)


# MongoDB Atlas
MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise EnvironmentError("MONGO_URI environment variable is not set")

MONGO_DB = os.getenv("MONGO_DB")
if not MONGO_DB:
    raise EnvironmentError("MONGO_DB environment variable is not set")

MONGO_COLLECTIONS = {
    "customers": "customers",
    "products": "products",
    "orders": "orders"
}