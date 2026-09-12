CREATE SCHEMA IF NOT EXISTS dwh;

-- Dimensions

CREATE TABLE dwh.dim_customer (
    customer_key SERIAL PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL UNIQUE,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(255),
    country VARCHAR(100),
    city VARCHAR(100),
    signup_date DATE,
    customer_segment VARCHAR(50)
);

CREATE TABLE dwh.dim_product (
    product_key SERIAL PRIMARY KEY,
    product_id VARCHAR(50) NOT NULL UNIQUE,
    product_name VARCHAR(255),
    category_id VARCHAR(50),
    category_name VARCHAR(100),
    brand VARCHAR(100),
    unit_cost NUMERIC(10, 2),
    unit_price NUMERIC(10, 2),
    stock_threshold INTEGER
);

CREATE TABLE dwh.dim_date (
    date_key INTEGER PRIMARY KEY,
    full_date DATE NOT NULL UNIQUE,
    year INTEGER NOT NULL,
    quarter INTEGER NOT NULL,
    month INTEGER NOT NULL,
    month_name VARCHAR(20) NOT NULL,
    day INTEGER NOT NULL,
    day_of_week INTEGER NOT NULL,
    day_name VARCHAR(20) NOT NULL,
    is_weekend BOOLEAN NOT NULL
);

CREATE TABLE dwh.dim_location (
    location_key SERIAL PRIMARY KEY,
    country VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE dwh.dim_warehouse (
    warehouse_key SERIAL PRIMARY KEY,
    warehouse_id VARCHAR(50) NOT NULL UNIQUE
);

-- Faits

CREATE TABLE dwh.fact_orders (
    order_key SERIAL PRIMARY KEY,
    order_id VARCHAR(50) NOT NULL UNIQUE,
    customer_key INTEGER NOT NULL REFERENCES dwh.dim_customer(customer_key),
    date_key INTEGER NOT NULL REFERENCES dwh.dim_date(date_key),
    location_key INTEGER REFERENCES dwh.dim_location(location_key),
    order_status VARCHAR(20),
    payment_method VARCHAR(50),
    total_amount NUMERIC(12, 2)
);

CREATE TABLE dwh.fact_order_items (
    order_item_key SERIAL PRIMARY KEY,
    order_item_id VARCHAR(50) NOT NULL UNIQUE,
    order_id VARCHAR(50) NOT NULL,
    product_key INTEGER NOT NULL REFERENCES dwh.dim_product(product_key),
    customer_key INTEGER NOT NULL REFERENCES dwh.dim_customer(customer_key),
    date_key INTEGER NOT NULL REFERENCES dwh.dim_date(date_key),
    quantity INTEGER,
    unit_price NUMERIC(10, 2),
    discount NUMERIC(10, 2)
);

CREATE TABLE dwh.fact_payments (
    payment_key SERIAL PRIMARY KEY,
    payment_id VARCHAR(50) NOT NULL UNIQUE,
    order_id VARCHAR(50) NOT NULL,
    date_key INTEGER NOT NULL REFERENCES dwh.dim_date(date_key),
    amount NUMERIC(12, 2),
    payment_method VARCHAR(50),
    payment_status VARCHAR(20),
    transaction_id VARCHAR(50)
);

CREATE TABLE dwh.fact_returns (
    return_key SERIAL PRIMARY KEY,
    return_id VARCHAR(50) NOT NULL UNIQUE,
    order_id VARCHAR(50) NOT NULL,
    product_key INTEGER NOT NULL REFERENCES dwh.dim_product(product_key),
    date_key INTEGER NOT NULL REFERENCES dwh.dim_date(date_key),
    quantity INTEGER,
    reason VARCHAR(100)
);

CREATE TABLE dwh.fact_inventory (
    inventory_key SERIAL PRIMARY KEY,
    inventory_id VARCHAR(50) NOT NULL UNIQUE,
    product_key INTEGER NOT NULL REFERENCES dwh.dim_product(product_key),
    warehouse_key INTEGER NOT NULL REFERENCES dwh.dim_warehouse(warehouse_key),
    date_key INTEGER NOT NULL REFERENCES dwh.dim_date(date_key),
    stock_quantity INTEGER
);