ALTER SESSION SET CONTAINER = XEPDB1;

CREATE TABLE raw_owner.ORDERS (
    order_id VARCHAR2(50),
    customer_id VARCHAR2(50),
    store_id VARCHAR2(50),
    order_date VARCHAR2(50),
    order_status VARCHAR2(50),
    currency VARCHAR2(10),
    total_amount VARCHAR2(50),
    created_at VARCHAR2(50),
    updated_at VARCHAR2(50),
    source_file VARCHAR2(200),
    source_system VARCHAR2(100),
    ingestion_timestamp TIMESTAMP DEFAULT SYSTIMESTAMP,
    batch_id VARCHAR2(50),
    record_hash VARCHAR2(64)
);

CREATE TABLE raw_owner.ORDER_ITEMS (
    order_item_id VARCHAR2(50),
    order_id VARCHAR2(50),
    product_id VARCHAR2(50),
    quantity VARCHAR2(50),
    unit_price VARCHAR2(50),
    discount_amount VARCHAR2(50),
    tax_amount VARCHAR2(50),
    source_file VARCHAR2(200),
    source_system VARCHAR2(100),
    ingestion_timestamp TIMESTAMP DEFAULT SYSTIMESTAMP,
    batch_id VARCHAR2(50),
    record_hash VARCHAR2(64)
);

CREATE TABLE raw_owner.CUSTOMERS (
    customer_id VARCHAR2(50),
    first_name VARCHAR2(100),
    last_name VARCHAR2(100),
    email VARCHAR2(200),
    phone VARCHAR2(50),
    city VARCHAR2(100),
    country VARCHAR2(100),
    registration_date VARCHAR2(50),
    customer_segment VARCHAR2(50),
    updated_at VARCHAR2(50),
    source_file VARCHAR2(200),
    source_system VARCHAR2(100),
    ingestion_timestamp TIMESTAMP DEFAULT SYSTIMESTAMP,
    batch_id VARCHAR2(50),
    record_hash VARCHAR2(64)
);

CREATE TABLE raw_owner.PRODUCTS (
    product_id VARCHAR2(50),
    product_name VARCHAR2(200),
    category VARCHAR2(100),
    subcategory VARCHAR2(100),
    brand VARCHAR2(100),
    supplier_id VARCHAR2(50),
    unit_cost VARCHAR2(50),
    list_price VARCHAR2(50),
    active_flag VARCHAR2(10),
    updated_at VARCHAR2(50),
    source_file VARCHAR2(200),
    source_system VARCHAR2(100),
    ingestion_timestamp TIMESTAMP DEFAULT SYSTIMESTAMP,
    batch_id VARCHAR2(50),
    record_hash VARCHAR2(64)
);

CREATE TABLE raw_owner.RETURNS (
    return_id VARCHAR2(50),
    order_item_id VARCHAR2(50),
    return_date VARCHAR2(50),
    return_reason VARCHAR2(200),
    return_quantity VARCHAR2(50),
    refund_amount VARCHAR2(50),
    source_file VARCHAR2(200),
    source_system VARCHAR2(100),
    ingestion_timestamp TIMESTAMP DEFAULT SYSTIMESTAMP,
    batch_id VARCHAR2(50),
    record_hash VARCHAR2(64)
);

CREATE TABLE raw_owner.STORES (
    store_id VARCHAR2(50),
    store_name VARCHAR2(200),
    store_type VARCHAR2(50),
    city VARCHAR2(100),
    country VARCHAR2(100),
    region VARCHAR2(100),
    opening_date VARCHAR2(50),
    source_file VARCHAR2(200),
    source_system VARCHAR2(100),
    ingestion_timestamp TIMESTAMP DEFAULT SYSTIMESTAMP,
    batch_id VARCHAR2(50)
);

CREATE TABLE raw_owner.SALES_TARGETS (
    store_id VARCHAR2(50),
    year VARCHAR2(10),
    month VARCHAR2(10),
    sales_target VARCHAR2(50),
    profit_target VARCHAR2(50),
    source_file VARCHAR2(200),
    source_system VARCHAR2(100),
    ingestion_timestamp TIMESTAMP DEFAULT SYSTIMESTAMP,
    batch_id VARCHAR2(50)
);