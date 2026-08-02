CREATE TABLE stg_owner.PRODUCTS_CLEAN (
    product_id VARCHAR2(50) PRIMARY KEY,
    product_name VARCHAR2(200),
    category VARCHAR2(100),
    subcategory VARCHAR2(100),
    brand VARCHAR2(100),
    supplier_id VARCHAR2(50),
    unit_cost NUMBER(12,2),
    list_price NUMBER(12,2),
    active_flag VARCHAR2(10),
    updated_at TIMESTAMP,
    batch_id VARCHAR2(50),
    loaded_at TIMESTAMP DEFAULT SYSTIMESTAMP
);