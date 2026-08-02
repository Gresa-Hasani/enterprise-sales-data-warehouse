-- Reject: quantity <= 0
INSERT INTO audit_owner.REJECTED_RECORDS
    (batch_id, source_table, record_key, rejection_reason, record_payload)
SELECT
    r.batch_id,
    'RAW.ORDER_ITEMS',
    r.order_item_id,
    'quantity is <= 0',
    JSON_OBJECT('order_item_id' VALUE r.order_item_id, 'quantity' VALUE r.quantity)
FROM raw_owner.ORDER_ITEMS r
WHERE TO_NUMBER(r.quantity) <= 0;

-- Reject: unit_price is negative
INSERT INTO audit_owner.REJECTED_RECORDS
    (batch_id, source_table, record_key, rejection_reason, record_payload)
SELECT
    r.batch_id,
    'RAW.ORDER_ITEMS',
    r.order_item_id,
    'unit_price is negative',
    JSON_OBJECT('order_item_id' VALUE r.order_item_id, 'unit_price' VALUE r.unit_price)
FROM raw_owner.ORDER_ITEMS r
WHERE TO_NUMBER(r.unit_price) < 0;

-- Reject: order_id not found in ORDERS_CLEAN
INSERT INTO audit_owner.REJECTED_RECORDS
    (batch_id, source_table, record_key, rejection_reason, record_payload)
SELECT
    r.batch_id,
    'RAW.ORDER_ITEMS',
    r.order_item_id,
    'order_id not found in ORDERS_CLEAN',
    JSON_OBJECT('order_item_id' VALUE r.order_item_id, 'order_id' VALUE r.order_id)
FROM raw_owner.ORDER_ITEMS r
WHERE NOT EXISTS (
    SELECT 1
    FROM stg_owner.ORDERS_CLEAN o
    WHERE o.order_id = r.order_id
);

-- Reject: product_id not found in PRODUCTS_CLEAN
INSERT INTO audit_owner.REJECTED_RECORDS
    (batch_id, source_table, record_key, rejection_reason, record_payload)
SELECT
    r.batch_id,
    'RAW.ORDER_ITEMS',
    r.order_item_id,
    'product_id not found in PRODUCTS_CLEAN',
    JSON_OBJECT('order_item_id' VALUE r.order_item_id, 'product_id' VALUE r.product_id)
FROM raw_owner.ORDER_ITEMS r
WHERE NOT EXISTS (
    SELECT 1
    FROM stg_owner.PRODUCTS_CLEAN p
    WHERE p.product_id = r.product_id
);

-- Load clean records
MERGE INTO stg_owner.ORDER_ITEMS_CLEAN tgt
USING (
    SELECT
        order_item_id,
        order_id,
        product_id,
        TO_NUMBER(quantity) AS quantity,
        TO_NUMBER(unit_price) AS unit_price,
        TO_NUMBER(discount_amount) AS discount_amount,
        TO_NUMBER(tax_amount) AS tax_amount,
        batch_id
    FROM (
        SELECT
            r.*,
            ROW_NUMBER() OVER (
                PARTITION BY r.order_item_id
                ORDER BY r.ingestion_timestamp DESC
            ) AS rn
        FROM raw_owner.ORDER_ITEMS r
        WHERE TO_NUMBER(r.quantity) > 0
          AND TO_NUMBER(r.unit_price) >= 0
          AND EXISTS (
              SELECT 1
              FROM stg_owner.ORDERS_CLEAN o
              WHERE o.order_id = r.order_id
          )
          AND EXISTS (
              SELECT 1
              FROM stg_owner.PRODUCTS_CLEAN p
              WHERE p.product_id = r.product_id
          )
    )
    WHERE rn = 1
) src
ON (tgt.order_item_id = src.order_item_id)
WHEN MATCHED THEN UPDATE SET
    tgt.order_id = src.order_id,
    tgt.product_id = src.product_id,
    tgt.quantity = src.quantity,
    tgt.unit_price = src.unit_price,
    tgt.discount_amount = src.discount_amount,
    tgt.tax_amount = src.tax_amount,
    tgt.batch_id = src.batch_id,
    tgt.loaded_at = SYSTIMESTAMP
WHEN NOT MATCHED THEN INSERT (
    order_item_id,
    order_id,
    product_id,
    quantity,
    unit_price,
    discount_amount,
    tax_amount,
    batch_id
) VALUES (
    src.order_item_id,
    src.order_id,
    src.product_id,
    src.quantity,
    src.unit_price,
    src.discount_amount,
    src.tax_amount,
    src.batch_id
);

COMMIT;