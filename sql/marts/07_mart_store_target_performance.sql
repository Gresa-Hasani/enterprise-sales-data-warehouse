CREATE TABLE mart_owner.STORE_TARGET_PERFORMANCE (
    store_id VARCHAR2(50),
    year NUMBER(4),
    month NUMBER(2),
    actual_sales NUMBER(14,2),
    sales_target NUMBER(14,2),
    target_variance NUMBER(14,2),
    target_achievement_percentage NUMBER(6,2),
    refreshed_at TIMESTAMP DEFAULT SYSTIMESTAMP,
    CONSTRAINT pk_store_target PRIMARY KEY (store_id, year, month)
);