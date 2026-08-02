CREATE TABLE stg_owner.RETURNS_CLEAN (
    return_id VARCHAR2(50) PRIMARY KEY,
    order_item_id VARCHAR2(50),
    return_date DATE,
    return_reason VARCHAR2(200),
    return_quantity NUMBER(10),
    refund_amount NUMBER(12,2),
    batch_id VARCHAR2(50),
    loaded_at TIMESTAMP DEFAULT SYSTIMESTAMP
);