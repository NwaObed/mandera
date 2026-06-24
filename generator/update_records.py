from datetime import datetime, timezone
from pymongo import MongoClient

from pathlib import Path
import sys

project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from config.mongo_settings import MONGO_URI, MONGO_DB, MONGO_COLLECTIONS
from config.settings import BATCH_SCHEDULE_HOURS
from config.settings import generate_batch_id

def batch_id_for_timestamp(ts: datetime) -> str:
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    else:
        ts = ts.astimezone(timezone.utc)

    date_part = ts.strftime("%Y_%m_%d")
    hour = ts.hour

    batch_number = 1
    for i, scheduled_hour in enumerate(BATCH_SCHEDULE_HOURS):
        if abs(hour - scheduled_hour) <= 1:
            batch_number = i + 1
            break
    else:
        batch_number = 1 if hour < 12 else 2

    return f"{date_part}_{hour:02d}_batch_0{batch_number}"

client = MongoClient(MONGO_URI)
db = client[MONGO_DB]

for name, coll_name in MONGO_COLLECTIONS.items():
    missing = db[coll_name].find(
        {"batch_id": {"$exists": False}, "created_at": {"$exists": True}}
    )
    updated = 0
    for doc in missing:
        batch_id = batch_id_for_timestamp(doc["created_at"])
        db[coll_name].update_one(
            {"_id": doc["_id"]},
            {"$set": {"batch_id": batch_id}}
        )
        updated += 1
    print(f"{coll_name}: updated {updated} documents")

client.close()

# print(batch_id_for_timestamp(datetime(2024, 6, 1, 10, 30, tzinfo=timezone.utc)))  # Expected: "2024_06_01_10_batch_01"

# original_batch_id = generate_batch_id
# print(original_batch_id())  # Example output: "2024_06_01_10_batch_01"