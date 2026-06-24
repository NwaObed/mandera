CREATE SCHEMA IF NOT EXISTS staging;

CREATE TABLE IF NOT EXISTS staging.customers_clean (
    customer_id   VARCHAR(50)  NOT NULL,
    name          VARCHAR(200) NOT NULL,
    email         VARCHAR(200),
    phone         VARCHAR(50),
    city          VARCHAR(100),
    address       VARCHAR(100),
    country       VARCHAR(100),
    batch_id      VARCHAR(50)  NOT NULL,
    created_at    TIMESTAMP    NOT NULL DEFAULT NOW()
);


CREATE TABLE IF NOT EXISTS staging.products_clean (
    product_id    VARCHAR(50)  NOT NULL,
    product_name  VARCHAR(200) NOT NULL,
    category      VARCHAR(100),
    price         NUMERIC(12,2),
    batch_id      VARCHAR(50)  NOT NULL,
    created_at    TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS staging.orders_clean (
    order_id       VARCHAR(50)  NOT NULL,
    customer_id    VARCHAR(50)  NOT NULL,
    product_id     VARCHAR(50)  NOT NULL,
    region         VARCHAR(100) NOT NULL,
    amount         NUMERIC(12,2) NOT NULL,
    quantity         NUMERIC(12,2) NOT NULL,
    payment_status VARCHAR(20)  NOT NULL,
    batch_id       VARCHAR(50)  NOT NULL,
    created_at     TIMESTAMP    NOT NULL DEFAULT NOW()
);
 