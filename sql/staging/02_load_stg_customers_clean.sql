-- Reject 1: customer_id is NULL
INSERT INTO audit_owner.REJECTED_RECORDS
    (batch_id, source_table, record_key, rejection_reason, record_payload)
SELECT
    r.batch_id,
    'RAW.CUSTOMERS',
    NVL(r.customer_id, 'NULL_ID_ROWID_' || r.ROWID),
    'customer_id is NULL',
    JSON_OBJECT(
        'customer_id' VALUE r.customer_id,
        'first_name' VALUE r.first_name,
        'last_name' VALUE r.last_name,
        'email' VALUE r.email
    )
FROM raw_owner.CUSTOMERS r
WHERE r.customer_id IS NULL;

-- Reject 2: invalid email format (simple regex check)
INSERT INTO audit_owner.REJECTED_RECORDS
    (batch_id, source_table, record_key, rejection_reason, record_payload)
SELECT
    r.batch_id,
    'RAW.CUSTOMERS',
    r.customer_id,
    'invalid email format',
    JSON_OBJECT(
        'customer_id' VALUE r.customer_id,
        'email' VALUE r.email
    )
FROM raw_owner.CUSTOMERS r
WHERE r.customer_id IS NOT NULL
  AND (r.email IS NULL
       OR NOT REGEXP_LIKE(r.email, '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'));

-- Load clean, deduplicated records into STG.CUSTOMERS_CLEAN
-- Dedup rule: keep the row with the latest updated_at per customer_id

MERGE INTO stg_owner.CUSTOMERS_CLEAN tgt
USING (
    SELECT
        customer_id,
        first_name,
        last_name,
        email,
        phone,
        city,
        country,
        TO_DATE(registration_date, 'YYYY-MM-DD') AS registration_date,
        customer_segment,
        TO_TIMESTAMP(updated_at, 'YYYY-MM-DD"T"HH24:MI:SS.FF6') AS updated_at,
        batch_id
    FROM (
        SELECT
            r.*,
            ROW_NUMBER() OVER (
                PARTITION BY r.customer_id
                ORDER BY TO_TIMESTAMP(r.updated_at, 'YYYY-MM-DD"T"HH24:MI:SS.FF6') DESC
            ) AS rn
        FROM raw_owner.CUSTOMERS r
        WHERE r.customer_id IS NOT NULL
          AND r.email IS NOT NULL
          AND REGEXP_LIKE(r.email, '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
    )
    WHERE rn = 1
) src
ON (tgt.customer_id = src.customer_id)
WHEN MATCHED THEN UPDATE SET
    tgt.first_name = src.first_name,
    tgt.last_name = src.last_name,
    tgt.email = src.email,
    tgt.phone = src.phone,
    tgt.city = src.city,
    tgt.country = src.country,
    tgt.registration_date = src.registration_date,
    tgt.customer_segment = src.customer_segment,
    tgt.updated_at = src.updated_at,
    tgt.batch_id = src.batch_id,
    tgt.loaded_at = SYSTIMESTAMP
WHEN NOT MATCHED THEN INSERT (
    customer_id, first_name, last_name, email, phone, city, country,
    registration_date, customer_segment, updated_at, batch_id
) VALUES (
    src.customer_id, src.first_name, src.last_name, src.email, src.phone,
    src.city, src.country, src.registration_date, src.customer_segment,
    src.updated_at, src.batch_id
);
COMMIT;