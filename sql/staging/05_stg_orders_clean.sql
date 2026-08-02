CREATE TABLE stg_owner.ORDERS_CLEAN (
    order_id VARCHAR2(50) PRIMARY KEY,
    customer_id VARCHAR2(50),
    store_id VARCHAR2(50),
    order_date DATE,
    order_status VARCHAR2(50),
    currency VARCHAR2(10),
    total_amount NUMBER(14,2),
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    batch_id VARCHAR2(50),
    loaded_at TIMESTAMP DEFAULT SYSTIMESTAMP
);