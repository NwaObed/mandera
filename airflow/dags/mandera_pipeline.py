"""
Mandera Analytics – Batch Pipeline DAG

Data generation is handled separately by GitHub Actions (8 AM & 4 PM WAT).
This DAG picks up whatever landed in MongoDB and processes it through:

  extract to MinIO → load raw tables → log monitoring counts →
  validate data quality → transform to staging → truncate raw

Schedule:
  - 08:30 AM WAT (07:30 UTC)
  - 04:30 PM WAT (15:30 UTC)
"""

import sys
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

sys.path.insert(0, "/opt/airflow")  # Project packages (extraction/, config/, …) are mounted here

from extraction.mongo_to_minio_pipeline import extract_to_minio
from extraction.mongo_to_postgres_pipeline import extract_to_postgres
from validation.validate_batch_counts import log_counts
from validation.validate_data_quality import validate
from transformation.transform_customers import (
    transform_customers,
    write as write_customers,
)
from transformation.transform_products import (
    transform as transform_products,
    write as write_products,
)
from transformation.transform_orders import (
    transform as transform_orders,
    write as write_orders,
)
from maintenance.truncate_raw_tables import truncate


# ── Failure callback ──────────────────────────────────────────
def on_task_failure(context):
    task = context["task_instance"]
    print(
        f"✗ TASK FAILED: {task.task_id} | "
        f"DAG: {task.dag_id} | "
        f"Execution: {context['execution_date']} | "
        f"Exception: {context.get('exception', 'N/A')}"
    )


# ── Task callables ────────────────────────────────────────────
def _extract_to_minio(**kwargs):
    counts = extract_to_minio()
    kwargs["ti"].xcom_push(key="minio_counts", value=counts)


def _extract_to_postgres(**kwargs):
    counts = extract_to_postgres()
    kwargs["ti"].xcom_push(key="pg_counts", value=counts)


def _log_monitoring(**kwargs):
    counts = kwargs["ti"].xcom_pull(task_ids="extract_to_postgres", key="pg_counts")
    log_counts(counts)


def _validate_quality(**kwargs):
    validate()


def _transform_customers(**kwargs):
    from sqlalchemy import create_engine
    from config.postgres_settings import POSTGRES_URL
    transform_customers(create_engine(POSTGRES_URL))


def _transform_products(**kwargs):
    from sqlalchemy import create_engine
    from config.postgres_settings import POSTGRES_URL
    transform_products(create_engine(POSTGRES_URL))


def _transform_orders(**kwargs):
    from sqlalchemy import create_engine
    from config.postgres_settings import POSTGRES_URL
    transform_orders(create_engine(POSTGRES_URL))


def _write_customers(**kwargs):
    from sqlalchemy import create_engine
    from config.postgres_settings import POSTGRES_URL
    write_customers(create_engine(POSTGRES_URL))


def _write_products(**kwargs):
    from sqlalchemy import create_engine
    from config.postgres_settings import POSTGRES_URL
    write_products(create_engine(POSTGRES_URL))


def _write_orders(**kwargs):
    from sqlalchemy import create_engine
    from config.postgres_settings import POSTGRES_URL
    write_orders(create_engine(POSTGRES_URL))


def _truncate_raw(**kwargs):
    truncate()




# ── DAG definition ────────────────────────────────────────────
default_args = {
    "owner": "Mandera_analytics_engineer",
    "depends_on_past": False,
    "email_on_failure": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "on_failure_callback": on_task_failure,
    "sla": timedelta(hours=1),
}

with DAG(
    dag_id="mandera_batch_pipeline",
    default_args=default_args,
    description="Analytics pipeline: MongoDB → MinIO + Postgres raw → staging",
    schedule_interval="30 7,15 * * *",
    start_date=datetime(2026, 3, 23),
    catchup=False,
    tags=["Mandera", "batch", "analytics"],
    max_active_runs=1,
) as dag:

    extract_minio = PythonOperator(
        task_id="extract_to_minio",
        python_callable=_extract_to_minio,
    )

    extract_postgres = PythonOperator(
        task_id="extract_to_postgres",
        python_callable=_extract_to_postgres,
    )

    log_monitoring = PythonOperator(
        task_id="log_monitoring",
        python_callable=_log_monitoring,
    )

    validate_quality = PythonOperator(
        task_id="validate_data_quality",
        python_callable=_validate_quality,
    )

    transform_cust = PythonOperator(
        task_id="transform_customers",
        python_callable=_transform_customers,
    )

    transform_prod = PythonOperator(
        task_id="transform_products",
        python_callable=_transform_products,
    )

    transform_ord = PythonOperator(
        task_id="transform_orders",
        python_callable=_transform_orders,
    )

    write_cust = PythonOperator(
        task_id="write_customers",
        python_callable=_write_customers,
    )

    write_prod = PythonOperator(
        task_id="write_products",
        python_callable=_write_products,
    )

    write_ord = PythonOperator(
        task_id="write_orders",
        python_callable=_write_orders,
    )

    truncate_raw = PythonOperator(
        task_id="truncate_raw_tables",
        python_callable=_truncate_raw,
    )

    # ── Task dependencies ─────────────────────────────────────
    # Write-Audit-Publish: transforms clean raw → staging_tmp (audit zone),
    # validation gates the audit zone, then writes publish staging_tmp →
    # staging. Nothing reaches published staging until validation passes.
    #
    # Extraction: MinIO and Postgres run in parallel
    [extract_minio, extract_postgres] >> log_monitoring

    # Transforms run in parallel, then a single validation gate over the
    # whole audit zone, then the per-entity publishes run in parallel.
    log_monitoring >> [transform_cust, transform_prod, transform_ord] >> validate_quality
    validate_quality >> [write_cust, write_prod, write_ord] >> truncate_raw