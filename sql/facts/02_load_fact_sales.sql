MERGE INTO dwh_owner.FACT_SALES tgt
USING (
    SELECT
        oi.order_item_id,
        o.order_id,
        TO_NUMBER(TO_CHAR(o.order_date, 'YYYYMMDD')) AS date_key,
        c.customer_key,
        p.product_key,
        s.store_key,
        ch.channel_key,
        st.status_key,
        oi.quantity,
        oi.unit_price,
        oi.quantity * oi.unit_price AS gross_amount,
        oi.discount_amount,
        oi.tax_amount,
        (oi.quantity * oi.unit_price) - oi.discount_amount + oi.tax_amount AS net_amount,
        oi.quantity * p.unit_cost AS cost_amount,
        ((oi.quantity * oi.unit_price) - oi.discount_amount + oi.tax_amount)
            - (oi.quantity * p.unit_cost) AS profit_amount,
        oi.batch_id
    FROM stg_owner.ORDER_ITEMS_CLEAN oi
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
    JOIN dwh_owner.DIM_ORDER_STATUS st
        ON st.status_code = o.order_status
    CROSS JOIN (
        SELECT channel_key
        FROM dwh_owner.DIM_SALES_CHANNEL
        WHERE channel_code = 'WEB'
    ) ch
) src
ON (tgt.order_item_id = src.order_item_id)
WHEN MATCHED THEN UPDATE SET
    tgt.order_id = src.order_id,
    tgt.date_key = src.date_key,
    tgt.customer_key = src.customer_key,
    tgt.product_key = src.product_key,
    tgt.store_key = src.store_key,
    tgt.channel_key = src.channel_key,
    tgt.status_key = src.status_key,
    tgt.quantity = src.quantity,
    tgt.unit_price = src.unit_price,
    tgt.gross_amount = src.gross_amount,
    tgt.discount_amount = src.discount_amount,
    tgt.tax_amount = src.tax_amount,
    tgt.net_amount = src.net_amount,
    tgt.cost_amount = src.cost_amount,
    tgt.profit_amount = src.profit_amount,
    tgt.batch_id = src.batch_id,
    tgt.loaded_at = SYSTIMESTAMP
WHEN NOT MATCHED THEN INSERT (
    order_id,
    order_item_id,
    date_key,
    customer_key,
    product_key,
    store_key,
    channel_key,
    status_key,
    quantity,
    unit_price,
    gross_amount,
    discount_amount,
    tax_amount,
    net_amount,
    cost_amount,
    profit_amount,
    batch_id
) VALUES (
    src.order_id,
    src.order_item_id,
    src.date_key,
    src.customer_key,
    src.product_key,
    src.store_key,
    src.channel_key,
    src.status_key,
    src.quantity,
    src.unit_price,
    src.gross_amount,
    src.discount_amount,
    src.tax_amount,
    src.net_amount,
    src.cost_amount,
    src.profit_amount,
    src.batch_id
);
COMMIT;