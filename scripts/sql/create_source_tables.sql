DROP TABLE IF EXISTS orders;
CREATE TABLE orders (
    order_id TEXT,
    customer_id TEXT,
    order_date TEXT,
    order_status TEXT,
    payment_method TEXT,
    shipping_country TEXT,
    total_amount NUMERIC
);

DROP TABLE IF EXISTS order_items;
CREATE TABLE order_items (
    order_item_id TEXT,
    order_id TEXT,
    product_id TEXT,
    quantity INTEGER,
    unit_price NUMERIC,
    discount NUMERIC
);

DROP TABLE IF EXISTS payments;
CREATE TABLE payments (
    payment_id TEXT,
    order_id TEXT,
    payment_date TEXT,
    payment_method TEXT,
    amount NUMERIC,
    payment_status TEXT,
    transaction_id TEXT
);
