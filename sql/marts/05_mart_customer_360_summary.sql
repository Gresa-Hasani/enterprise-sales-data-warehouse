CREATE TABLE mart_owner.CUSTOMER_360_SUMMARY (
    customer_id VARCHAR2(50) PRIMARY KEY,
    lifetime_value NUMBER(14,2),
    total_orders NUMBER,
    total_spent NUMBER(14,2),
    average_order_value NUMBER(14,2),
    first_order_date DATE,
    last_order_date DATE,
    preferred_category VARCHAR2(100),
    return_rate NUMBER(6,2),
    refreshed_at TIMESTAMP DEFAULT SYSTIMESTAMP
);