-- Reject: customer_id is NULL
INSERT INTO audit_owner.REJECTED_RECORDS
    (batch_id, source_table, record_key, rejection_reason, record_payload)
SELECT
    r.batch_id,
    'RAW.ORDERS',
    r.order_id,
    'customer_id is NULL',
    JSON_OBJECT('order_id' VALUE r.order_id)
FROM raw_owner.ORDERS r
WHERE r.customer_id IS NULL;

-- Reject: order_date is in the future
INSERT INTO audit_owner.REJECTED_RECORDS
    (batch_id, source_table, record_key, rejection_reason, record_payload)
SELECT
    r.batch_id,
    'RAW.ORDERS',
    r.order_id,
    'order_date is in the future',
    JSON_OBJECT('order_id' VALUE r.order_id, 'order_date' VALUE r.order_date)
FROM raw_owner.ORDERS r
WHERE TO_DATE(r.order_date, 'YYYY-MM-DD') > TRUNC(SYSDATE);

-- Reject: unknown currency
INSERT INTO audit_owner.REJECTED_RECORDS
    (batch_id, source_table, record_key, rejection_reason, record_payload)
SELECT
    r.batch_id,
    'RAW.ORDERS',
    r.order_id,
    'unknown currency',
    JSON_OBJECT('order_id' VALUE r.order_id, 'currency' VALUE r.currency)
FROM raw_owner.ORDERS r
WHERE r.currency NOT IN ('USD', 'EUR', 'GBP');

-- Reject: customer_id does not exist in STG.CUSTOMERS_CLEAN
INSERT INTO audit_owner.REJECTED_RECORDS
    (batch_id, source_table, record_key, rejection_reason, record_payload)
SELECT
    r.batch_id,
    'RAW.ORDERS',
    r.order_id,
    'customer_id not found in CUSTOMERS_CLEAN',
    JSON_OBJECT('order_id' VALUE r.order_id, 'customer_id' VALUE r.customer_id)
FROM raw_owner.ORDERS r
WHERE r.customer_id IS NOT NULL
  AND NOT EXISTS (
      SELECT 1
      FROM stg_owner.CUSTOMERS_CLEAN c
      WHERE c.customer_id = r.customer_id
  );

-- Load clean, deduplicated records (keep latest by updated_at per order_id)
MERGE INTO stg_owner.ORDERS_CLEAN tgt
USING (
    SELECT
        order_id,
        customer_id,
        store_id,
        TO_DATE(order_date, 'YYYY-MM-DD') AS order_date,
        order_status,
        currency,
        TO_NUMBER(total_amount) AS total_amount,
        TO_TIMESTAMP(created_at, 'YYYY-MM-DD"T"HH24:MI:SS.FF6') AS created_at,
        TO_TIMESTAMP(updated_at, 'YYYY-MM-DD"T"HH24:MI:SS.FF6') AS updated_at,
        batch_id
    FROM (
        SELECT
            r.*,
            ROW_NUMBER() OVER (
                PARTITION BY r.order_id
                ORDER BY TO_TIMESTAMP(r.updated_at, 'YYYY-MM-DD"T"HH24:MI:SS.FF6') DESC
            ) AS rn
        FROM raw_owner.ORDERS r
        WHERE r.customer_id IS NOT NULL
          AND TO_DATE(r.order_date, 'YYYY-MM-DD') <= TRUNC(SYSDATE)
          AND r.currency IN ('USD', 'EUR', 'GBP')
          AND EXISTS (
              SELECT 1
              FROM stg_owner.CUSTOMERS_CLEAN c
              WHERE c.customer_id = r.customer_id
          )
    )
    WHERE rn = 1
) src
ON (tgt.order_id = src.order_id)
WHEN MATCHED THEN UPDATE SET
    tgt.customer_id = src.customer_id,
    tgt.store_id = src.store_id,
    tgt.order_date = src.order_date,
    tgt.order_status = src.order_status,
    tgt.currency = src.currency,
    tgt.total_amount = src.total_amount,
    tgt.created_at = src.created_at,
    tgt.updated_at = src.updated_at,
    tgt.batch_id = src.batch_id,
    tgt.loaded_at = SYSTIMESTAMP
WHEN NOT MATCHED THEN INSERT (
    order_id,
    customer_id,
    store_id,
    order_date,
    order_status,
    currency,
    total_amount,
    created_at,
    updated_at,
    batch_id
) VALUES (
    src.order_id,
    src.customer_id,
    src.store_id,
    src.order_date,
    src.order_status,
    src.currency,
    src.total_amount,
    src.created_at,
    src.updated_at,
    src.batch_id
);

COMMIT;