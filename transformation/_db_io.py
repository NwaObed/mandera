"""
Version-independent database I/O for the transforms.

pandas' read_sql/to_sql route through a SQLAlchemy-version check: modern
pandas demands SQLAlchemy >= 2.0, but Airflow 2.x hard-pins SQLAlchemy to
1.4. To work in BOTH the host venv (SQLAlchemy 2.0) and the Airflow
container (1.4), we avoid pandas' SQL I/O entirely:

  - reads  go through SQLAlchemy Core (works on 1.4 and 2.0)
  - writes go through psycopg2 COPY (raw connection; also sidesteps numpy
    type-adaptation since COPY transfers CSV text that Postgres parses)
"""

import io

import pandas as pd
from sqlalchemy import text


def read_table(engine, table):
    """Read an entire table into a DataFrame using SQLAlchemy Core."""
    with engine.connect() as conn:
        result = conn.execute(text(f"SELECT * FROM {table}"))
        return pd.DataFrame(result.mappings().all())


def replace_table(engine, table, df, columns):
    """
    Truncate `table` and bulk-load df[columns] via COPY.

    Empty CSV fields are treated as SQL NULL, so NaN/NaT become NULL.
    """
    buf = io.StringIO()
    df[columns].to_csv(buf, index=False, header=False, na_rep="")
    buf.seek(0)

    col_list = ", ".join(columns)
    raw = engine.raw_connection()
    try:
        with raw.cursor() as cur:
            cur.execute(f"TRUNCATE {table}")
            cur.copy_expert(
                f"COPY {table} ({col_list}) FROM STDIN WITH (FORMAT csv, NULL '')",
                buf,
            )
        raw.commit()
    finally:
        raw.close()