-- Reject: negative list_price
INSERT INTO audit_owner.REJECTED_RECORDS
    (batch_id, source_table, record_key, rejection_reason, record_payload)
SELECT
    r.batch_id,
    'RAW.PRODUCTS',
    r.product_id,
    'list_price is negative',
    JSON_OBJECT('product_id' VALUE r.product_id, 'list_price' VALUE r.list_price)
FROM raw_owner.PRODUCTS r
WHERE TO_NUMBER(r.list_price) < 0;

-- Reject: negative unit_cost
INSERT INTO audit_owner.REJECTED_RECORDS
    (batch_id, source_table, record_key, rejection_reason, record_payload)
SELECT
    r.batch_id,
    'RAW.PRODUCTS',
    r.product_id,
    'unit_cost is negative',
    JSON_OBJECT('product_id' VALUE r.product_id, 'unit_cost' VALUE r.unit_cost)
FROM raw_owner.PRODUCTS r
WHERE TO_NUMBER(r.unit_cost) < 0;

-- Reject: category is NULL
INSERT INTO audit_owner.REJECTED_RECORDS
    (batch_id, source_table, record_key, rejection_reason, record_payload)
SELECT
    r.batch_id,
    'RAW.PRODUCTS',
    r.product_id,
    'category is NULL',
    JSON_OBJECT('product_id' VALUE r.product_id)
FROM raw_owner.PRODUCTS r
WHERE r.category IS NULL;

-- Load clean, deduplicated records (keep latest by updated_at per product_id)
MERGE INTO stg_owner.PRODUCTS_CLEAN tgt
USING (
    SELECT
        product_id,
        product_name,
        category,
        subcategory,
        brand,
        supplier_id,
        TO_NUMBER(unit_cost) AS unit_cost,
        TO_NUMBER(list_price) AS list_price,
        active_flag,
        TO_TIMESTAMP(updated_at, 'YYYY-MM-DD"T"HH24:MI:SS.FF6') AS updated_at,
        batch_id
    FROM (
        SELECT
            r.*,
            ROW_NUMBER() OVER (
                PARTITION BY r.product_id
                ORDER BY TO_TIMESTAMP(r.updated_at, 'YYYY-MM-DD"T"HH24:MI:SS.FF6') DESC
            ) AS rn
        FROM raw_owner.PRODUCTS r
        WHERE r.category IS NOT NULL
          AND TO_NUMBER(r.list_price) >= 0
          AND TO_NUMBER(r.unit_cost) >= 0
    )
    WHERE rn = 1
) src
ON (tgt.product_id = src.product_id)
WHEN MATCHED THEN UPDATE SET
    tgt.product_name = src.product_name,
    tgt.category = src.category,
    tgt.subcategory = src.subcategory,
    tgt.brand = src.brand,
    tgt.supplier_id = src.supplier_id,
    tgt.unit_cost = src.unit_cost,
    tgt.list_price = src.list_price,
    tgt.active_flag = src.active_flag,
    tgt.updated_at = src.updated_at,
    tgt.batch_id = src.batch_id,
    tgt.loaded_at = SYSTIMESTAMP
WHEN NOT MATCHED THEN INSERT (
    product_id,
    product_name,
    category,
    subcategory,
    brand,
    supplier_id,
    unit_cost,
    list_price,
    active_flag,
    updated_at,
    batch_id
) VALUES (
    src.product_id,
    src.product_name,
    src.category,
    src.subcategory,
    src.brand,
    src.supplier_id,
    src.unit_cost,
    src.list_price,
    src.active_flag,
    src.updated_at,
    src.batch_id
);

COMMIT;