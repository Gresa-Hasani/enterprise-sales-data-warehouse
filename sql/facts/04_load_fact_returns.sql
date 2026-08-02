MERGE INTO dwh_owner.FACT_RETURNS tgt
USING (
    SELECT
        ret.return_id,
        ret.order_item_id,
        TO_NUMBER(TO_CHAR(ret.return_date, 'YYYYMMDD')) AS return_date_key,
        c.customer_key,
        p.product_key,
        s.store_key,
        ret.return_quantity,
        ret.refund_amount,
        ret.return_reason,
        ret.batch_id
    FROM stg_owner.RETURNS_CLEAN ret
    JOIN stg_owner.ORDER_ITEMS_CLEAN oi
        ON oi.order_item_id = ret.order_item_id
    JOIN stg_owner.ORDERS_CLEAN o
        ON o.order_id = oi.order_id
    JOIN dwh_owner.DIM_CUSTOMER c
        ON c.customer_id = o.customer_id
       AND c.is_current = 1
    JOIN dwh_owner.DIM_PRODUCT p
        ON p.product_id = oi.product_id
       AND p.is_current = 1
    JOIN dwh_owner.DIM_STORE s
        ON s.store_id = o.store_id
) src
ON (tgt.return_id = src.return_id)
WHEN MATCHED THEN UPDATE SET
    tgt.order_item_id = src.order_item_id,
    tgt.return_date_key = src.return_date_key,
    tgt.customer_key = src.customer_key,
    tgt.product_key = src.product_key,
    tgt.store_key = src.store_key,
    tgt.return_quantity = src.return_quantity,
    tgt.refund_amount = src.refund_amount,
    tgt.return_reason = src.return_reason,
    tgt.batch_id = src.batch_id,
    tgt.loaded_at = SYSTIMESTAMP
WHEN NOT MATCHED THEN INSERT (
    return_id,
    order_item_id,
    return_date_key,
    customer_key,
    product_key,
    store_key,
    return_quantity,
    refund_amount,
    return_reason,
    batch_id
) VALUES (
    src.return_id,
    src.order_item_id,
    src.return_date_key,
    src.customer_key,
    src.product_key,
    src.store_key,
    src.return_quantity,
    src.refund_amount,
    src.return_reason,
    src.batch_id
);
COMMIT;