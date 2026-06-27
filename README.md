# Mandera Analytics Pipeline

Mandera is a batch data pipeline that turns synthetic commerce records into trusted, analytics-ready datasets. Python and Faker generate customers, products, and orders in MongoDB Atlas; Apache Airflow then archives the data in MinIO, loads it into PostgreSQL, validates it, transforms it, and clears the raw landing tables for the next batch.

## Business problem being solved

Mandera Analytics receives growing volumes of operational transaction data that are not consistently preserved, validated, or prepared for reporting. Manual and unstructured loading processes make missing records, duplicates, and unusual batch volumes difficult to detect, resulting in slow reporting, weak reconciliation, and low confidence in analytical data.

## Delivered outcome

This project delivers a repeatable, Airflow-orchestrated batch pipeline that:

- Generates realistic transactional data with traceable batch IDs
- Preserves source records in MongoDB Atlas and partitioned MinIO storage
- Loads and monitors PostgreSQL raw landing tables
- Validates data quality and batch completeness before publication
- Produces trusted staging tables for analytics and reporting
- Truncates raw tables only after successful transformation

## Pipeline

```text
Python + Faker → MongoDB Atlas ─┬→ MinIO (partitioned JSON archive)
                               └→ PostgreSQL raw → audit/validation → staging
                                                        ↓
                                                truncate raw tables
```

Each record receives a batch ID. Row counts and batch variance are recorded to support reconciliation and anomaly detection. The Airflow DAG runs at 08:30 and 16:30 WAT, after scheduled data generation at 08:00 and 16:00 WAT.

## Technology

Python, Faker, MongoDB Atlas, MinIO, PostgreSQL, Pandas, Apache Airflow, Redis, Docker Compose, and GitHub Actions.

## How to use

### 1. Prerequisites

- Docker with Docker Compose
- A MongoDB Atlas database
- Git

### 2. Clone and configure

```bash
git clone https://github.com/NwaObed/mandera.git
cd mandera
```

Create a `.env` file:

```dotenv
MONGO_URI=mongodb+srv://<user>:<password>@<cluster>/
MONGO_DB=mandera

POSTGRES_USER=mandera
POSTGRES_PASSWORD=<password>
POSTGRES_DB=mandera
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_EXTERNAL_PORT=5433

MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=<password>
MINIO_ENDPOINT=http://minio:9000
MINIO_BUCKET=mandera-raw

PGADMIN_EMAIL=admin@example.com
PGADMIN_PASSWORD=<password>

AIRFLOW__CORE__EXECUTOR=CeleryExecutor
AIRFLOW__CORE__SQL_ALCHEMY_CONN=postgresql+psycopg2://mandera:<password>@postgres:5432/mandera
AIRFLOW__CELERY__BROKER_URL=redis://redis:6379/0
AIRFLOW__CELERY__RESULT_BACKEND=db+postgresql://mandera:<password>@postgres:5432/mandera
AIRFLOW__CORE__FERNET_KEY=<generated-fernet-key>
AIRFLOW__CORE__LOAD_EXAMPLES=False
```

Generate a Fernet key with:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 3. Start the services

```bash
docker compose build
docker compose up -d postgres redis minio pgadmin
docker compose run --rm db-setup
docker compose up -d airflow-webserver airflow-scheduler airflow-worker
```

Open:

- Airflow: <http://localhost:8080> (`admin` / `admin`)
- MinIO console: <http://localhost:9001>
- pgAdmin: <http://localhost:5000>

### 4. Generate and process data

Generate a batch locally:

```bash
python -m pip install -r requirements.txt
python -m generator.data_generator
```

In Airflow, enable or manually trigger the `mandera_batch_pipeline` DAG. It will extract to MinIO and PostgreSQL, log counts, transform and validate the data, publish clean staging tables, and truncate the raw tables after success.

For scheduled generation, add `MONGO_URI` and `MONGO_DB` as GitHub Actions secrets; the included workflow runs twice daily and also supports manual dispatch.

## Project structure

```text
airflow/dags/    Airflow orchestration
generator/       Synthetic data generation
extraction/      MongoDB-to-MinIO/PostgreSQL ingestion
transformation/  Raw-to-staging transformations
validation/      Quality and batch-count checks
maintenance/     Raw-table cleanup
sql/             Warehouse schema definitions
config/          Service configuration
```

