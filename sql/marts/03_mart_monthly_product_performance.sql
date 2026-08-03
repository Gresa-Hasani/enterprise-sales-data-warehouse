CREATE TABLE mart_owner.MONTHLY_PRODUCT_PERFORMANCE (
    year NUMBER(4),
    month NUMBER(2),
    product_id VARCHAR2(50),
    product_name VARCHAR2(200),
    category VARCHAR2(100),
    revenue NUMBER(14,2),
    profit NUMBER(14,2),
    units_sold NUMBER,
    units_returned NUMBER,
    return_rate NUMBER(6,2),
    refreshed_at TIMESTAMP DEFAULT SYSTIMESTAMP,
    CONSTRAINT uq_monthly_product UNIQUE (year, month, product_id)
);