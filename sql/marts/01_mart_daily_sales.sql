CREATE TABLE mart_owner.DAILY_SALES (
    sales_date DATE,
    store_id VARCHAR2(50),
    store_name VARCHAR2(200),
    channel_code VARCHAR2(20),
    gross_sales NUMBER(14,2),
    net_sales NUMBER(14,2),
    profit NUMBER(14,2),
    order_count NUMBER,
    customer_count NUMBER,
    units_sold NUMBER,
    refreshed_at TIMESTAMP DEFAULT SYSTIMESTAMP,
    CONSTRAINT uq_daily_sales UNIQUE (sales_date, store_id, channel_code)
);