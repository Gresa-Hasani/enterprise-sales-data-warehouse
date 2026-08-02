-- Run once: create the clean table structure
CREATE TABLE stg_owner.CUSTOMERS_CLEAN (
    customer_id VARCHAR2(50)  PRIMARY KEY,
    first_name VARCHAR2(100),
    last_name VARCHAR2(100),
    email VARCHAR2(200),
    phone VARCHAR2(50),
    city VARCHAR2(100),
    country VARCHAR2(100),
    registration_date DATE,
    customer_segment VARCHAR2(50),
    updated_at TIMESTAMP,
    batch_id VARCHAR2(50),
    loaded_at TIMESTAMP DEFAULT SYSTIMESTAMP
);