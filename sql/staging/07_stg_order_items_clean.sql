CREATE TABLE stg_owner.ORDER_ITEMS_CLEAN (
    order_item_id VARCHAR2(50) PRIMARY KEY,
    order_id VARCHAR2(50),
    product_id VARCHAR2(50),
    quantity NUMBER(10),
    unit_price NUMBER(12,2),
    discount_amount NUMBER(12,2),
    tax_amount NUMBER(12,2),
    batch_id VARCHAR2(50),
    loaded_at TIMESTAMP DEFAULT SYSTIMESTAMP
);