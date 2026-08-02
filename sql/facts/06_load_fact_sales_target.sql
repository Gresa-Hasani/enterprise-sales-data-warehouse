MERGE INTO dwh_owner.FACT_SALES_TARGET tgt
USING (
    SELECT store_key, month_date_key, sales_target, profit_target, batch_id
    FROM (
        SELECT
            s.store_key,
            TO_NUMBER(t.year || LPAD(t.month, 2, '0') || '01') AS month_date_key,
            TO_NUMBER(t.sales_target)  AS sales_target,
            TO_NUMBER(t.profit_target) AS profit_target,
            t.batch_id,
            ROW_NUMBER() OVER (
                PARTITION BY s.store_key, TO_NUMBER(t.year || LPAD(t.month, 2, '0') || '01')
                ORDER BY t.ingestion_timestamp DESC
            ) AS rn
        FROM raw_owner.SALES_TARGETS t
        JOIN dwh_owner.DIM_STORE s ON s.store_id = t.store_id
    )
    WHERE rn = 1
) src
ON (tgt.store_key = src.store_key AND tgt.month_date_key = src.month_date_key)
WHEN MATCHED THEN UPDATE SET
    tgt.sales_target  = src.sales_target,
    tgt.profit_target = src.profit_target,
    tgt.batch_id      = src.batch_id,
    tgt.loaded_at     = SYSTIMESTAMP
WHEN NOT MATCHED THEN INSERT (
    store_key, month_date_key, sales_target, profit_target, batch_id
) VALUES (
    src.store_key, src.month_date_key, src.sales_target, src.profit_target, src.batch_id
);

COMMIT;