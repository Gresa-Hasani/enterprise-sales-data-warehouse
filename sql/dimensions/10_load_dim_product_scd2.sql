-- Step 1: close out current versions whose hash has changed
UPDATE dwh_owner.DIM_PRODUCT tgt
SET
    effective_to = TRUNC(SYSDATE) - 1,
    is_current = 0
WHERE is_current = 1
  AND EXISTS (
      SELECT 1
      FROM stg_owner.PRODUCTS_CLEAN src
      WHERE src.product_id = tgt.product_id
        AND STANDARD_HASH(
            src.product_name || '|' || src.category || '|' || src.subcategory ||
            '|' || src.brand || '|' || TO_CHAR(src.unit_cost) || '|' || TO_CHAR(src.list_price),
            'SHA256'
        ) != tgt.record_hash
  );

-- Step 2: insert new products AND new versions of changed products
INSERT INTO dwh_owner.DIM_PRODUCT (
    product_id,
    product_name,
    category,
    subcategory,
    brand,
    supplier_id,
    unit_cost,
    list_price,
    effective_from,
    effective_to,
    is_current,
    record_hash
)
SELECT
    src.product_id,
    src.product_name,
    src.category,
    src.subcategory,
    src.brand,
    src.supplier_id,
    src.unit_cost,
    src.list_price,
    TRUNC(SYSDATE) AS effective_from,
    NULL AS effective_to,
    1 AS is_current,
    STANDARD_HASH(
        src.product_name || '|' || src.category || '|' || src.subcategory ||
        '|' || src.brand || '|' || TO_CHAR(src.unit_cost) || '|' || TO_CHAR(src.list_price),
        'SHA256'
    ) AS record_hash
FROM stg_owner.PRODUCTS_CLEAN src
WHERE NOT EXISTS (
    SELECT 1
    FROM dwh_owner.DIM_PRODUCT tgt
    WHERE tgt.product_id = src.product_id
      AND tgt.is_current = 1
);
COMMIT;