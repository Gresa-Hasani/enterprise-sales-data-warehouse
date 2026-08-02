MERGE INTO dwh_owner.DIM_STORE tgt
USING (
    SELECT
        store_id,
        store_name,
        store_type,
        city,
        country,
        region,
        TO_DATE(opening_date, 'YYYY-MM-DD') AS opening_date
    FROM raw_owner.STORES
) src
ON (tgt.store_id = src.store_id)
WHEN MATCHED THEN UPDATE SET
    tgt.store_name = src.store_name,
    tgt.store_type = src.store_type,
    tgt.city = src.city,
    tgt.country = src.country,
    tgt.region = src.region,
    tgt.opening_date = src.opening_date
WHEN NOT MATCHED THEN INSERT (
    store_id,
    store_name,
    store_type,
    city,
    country,
    region,
    opening_date
) VALUES (
    src.store_id,
    src.store_name,
    src.store_type,
    src.city,
    src.country,
    src.region,
    src.opening_date
);
COMMIT;