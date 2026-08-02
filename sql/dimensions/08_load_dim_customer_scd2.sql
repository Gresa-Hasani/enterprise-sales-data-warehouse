-- Step 1: close out current versions whose hash has changed
UPDATE dwh_owner.DIM_CUSTOMER tgt
SET
    effective_to = TRUNC(SYSDATE) - 1,
    is_current = 0
WHERE is_current = 1
  AND EXISTS (
      SELECT 1
      FROM stg_owner.CUSTOMERS_CLEAN src
      WHERE src.customer_id = tgt.customer_id
        AND STANDARD_HASH(
            src.first_name || '|' || src.last_name || '|' ||
            src.email || '|' || src.city || '|' || src.customer_segment,
            'SHA256'
        ) != tgt.record_hash
  );

-- Step 2: insert new customers AND new versions of changed customers
INSERT INTO dwh_owner.DIM_CUSTOMER (
    customer_id,
    first_name,
    last_name,
    email,
    phone,
    city,
    country,
    customer_segment,
    registration_date,
    effective_from,
    effective_to,
    is_current,
    record_hash
)
SELECT
    src.customer_id,
    src.first_name,
    src.last_name,
    src.email,
    src.phone,
    src.city,
    src.country,
    src.customer_segment,
    src.registration_date,
    TRUNC(SYSDATE) AS effective_from,
    NULL AS effective_to,
    1 AS is_current,
    STANDARD_HASH(
        src.first_name || '|' || src.last_name || '|' ||
        src.email || '|' || src.city || '|' || src.customer_segment,
        'SHA256'
    ) AS record_hash
FROM stg_owner.CUSTOMERS_CLEAN src
WHERE NOT EXISTS (
    SELECT 1
    FROM dwh_owner.DIM_CUSTOMER tgt
    WHERE tgt.customer_id = src.customer_id
      AND tgt.is_current = 1
);
COMMIT;