"""
Logs row counts and variance to monitoring.batch_log.

Compares source_rows (extracted from MongoDB) against loaded_rows
(inserted into raw tables) to detect data loss during ingestion.
"""

from datetime import datetime, timezone

import psycopg2

from config.postgres_settings import POSTGRES_CONFIG, RAW_TABLES


def log_counts(counts: dict):
    """
    Write monitoring rows for the current pipeline run.

    Args:
        counts: {"customers": {"source_rows": 15, "loaded_rows": 15}, ...}
    """
    conn = psycopg2.connect(**POSTGRES_CONFIG)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    try:
        with conn.cursor() as cur:
            for table_name, row_counts in counts.items():
                source = row_counts["source_rows"]
                loaded = row_counts["loaded_rows"]
                variance = source - loaded

                cur.execute(
                    """
                    INSERT INTO monitoring.batch_log
                        (run_id, table_name, source_rows, loaded_rows, variance)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (run_id, RAW_TABLES[table_name], source, loaded, variance),
                )

                status = "✓" if variance == 0 else "⚠"
                print(
                    f"  {status} {table_name}: source={source}, "
                    f"loaded={loaded}, variance={variance}"
                )
        conn.commit()
        print(f"  ✓ Monitoring log saved (run: {run_id})")
    finally:
        conn.close()