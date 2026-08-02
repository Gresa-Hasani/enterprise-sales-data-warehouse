-- Reject: return_quantity <= 0
INSERT INTO audit_owner.REJECTED_RECORDS
    (batch_id, source_table, record_key, rejection_reason, record_payload)
SELECT
    r.batch_id,
    'RAW.RETURNS',
    r.return_id,
    'return_quantity is <= 0',
    JSON_OBJECT('return_id' VALUE r.return_id, 'return_quantity' VALUE r.return_quantity)
FROM raw_owner.RETURNS r
WHERE TO_NUMBER(r.return_quantity) <= 0;

-- Reject: refund_amount is negative
INSERT INTO audit_owner.REJECTED_RECORDS
    (batch_id, source_table, record_key, rejection_reason, record_payload)
SELECT
    r.batch_id,
    'RAW.RETURNS',
    r.return_id,
    'refund_amount is negative',
    JSON_OBJECT('return_id' VALUE r.return_id, 'refund_amount' VALUE r.refund_amount)
FROM raw_owner.RETURNS r
WHERE TO_NUMBER(r.refund_amount) < 0;

-- Reject: order_item_id not found in ORDER_ITEMS_CLEAN
INSERT INTO audit_owner.REJECTED_RECORDS
    (batch_id, source_table, record_key, rejection_reason, record_payload)
SELECT
    r.batch_id,
    'RAW.RETURNS',
    r.return_id,
    'order_item_id not found in ORDER_ITEMS_CLEAN',
    JSON_OBJECT('return_id' VALUE r.return_id, 'order_item_id' VALUE r.order_item_id)
FROM raw_owner.RETURNS r
WHERE NOT EXISTS (
    SELECT 1
    FROM stg_owner.ORDER_ITEMS_CLEAN oi
    WHERE oi.order_item_id = r.order_item_id
);

-- Load clean records
MERGE INTO stg_owner.RETURNS_CLEAN tgt
USING (
    SELECT
        return_id,
        order_item_id,
        TO_DATE(return_date, 'YYYY-MM-DD') AS return_date,
        return_reason,
        TO_NUMBER(return_quantity) AS return_quantity,
        TO_NUMBER(refund_amount) AS refund_amount,
        batch_id
    FROM (
        SELECT
            r.*,
            ROW_NUMBER() OVER (
                PARTITION BY r.return_id
                ORDER BY r.ingestion_timestamp DESC
            ) AS rn
        FROM raw_owner.RETURNS r
        WHERE TO_NUMBER(r.return_quantity) > 0
          AND TO_NUMBER(r.refund_amount) >= 0
          AND EXISTS (
              SELECT 1
              FROM stg_owner.ORDER_ITEMS_CLEAN oi
              WHERE oi.order_item_id = r.order_item_id
          )
    )
    WHERE rn = 1
) src
ON (tgt.return_id = src.return_id)
WHEN MATCHED THEN UPDATE SET
    tgt.order_item_id = src.order_item_id,
    tgt.return_date = src.return_date,
    tgt.return_reason = src.return_reason,
    tgt.return_quantity = src.return_quantity,
    tgt.refund_amount = src.refund_amount,
    tgt.batch_id = src.batch_id,
    tgt.loaded_at = SYSTIMESTAMP
WHEN NOT MATCHED THEN INSERT (
    return_id,
    order_item_id,
    return_date,
    return_reason,
    return_quantity,
    refund_amount,
    batch_id
) VALUES (
    src.return_id,
    src.order_item_id,
    src.return_date,
    src.return_reason,
    src.return_quantity,
    src.refund_amount,
    src.batch_id
);
COMMIT;