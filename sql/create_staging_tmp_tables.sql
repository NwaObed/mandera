-- Audit zone for the Write-Audit-Publish flow.
--
-- Transforms write their cleaned output here; validate_data_quality runs
-- against these tables; only if validation passes do the write tasks
-- promote rows into the published staging.*_clean tables.
--
-- These tables are intentionally LENIENT (no NOT NULL, no PK): if a buggy
-- transform emits bad rows, they must still land here so validation can
-- catch and report them — rather than the load failing on a constraint
-- before validation ever runs.
CREATE SCHEMA IF NOT EXISTS staging_tmp;

CREATE SCHEMA IF NOT EXISTS staging;

CREATE TABLE IF NOT EXISTS staging.customers_clean (
    customer_id   TEXT,
    name          TEXT,
    email         TEXT,
    phone         TEXT,
    city          TEXT,
    address       TEXT,
    country       TEXT,
    batch_id      TEXT,
    created_at    TIMESTAMP
);


CREATE TABLE IF NOT EXISTS staging.products_clean (
    product_id    TEXT,
    product_name  TEXT,
    category      TEXT,
    price         NUMERIC(12,2),
    batch_id      TEXT,
    created_at    TIMESTAMP
);

CREATE TABLE IF NOT EXISTS staging.orders_clean (
    order_id       TEXT,
    customer_id    TEXT,
    product_id     TEXT,
    region         TEXT,
    amount         NUMERIC,
    quantity         NUMERIC,
    payment_status TEXT,
    batch_id       TEXT,
    created_at     TIMESTAMP
);
 