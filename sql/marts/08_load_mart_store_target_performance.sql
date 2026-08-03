TRUNCATE TABLE mart_owner.STORE_TARGET_PERFORMANCE;

INSERT INTO mart_owner.STORE_TARGET_PERFORMANCE (
    store_id,
    year,
    month,
    actual_sales,
    sales_target,
    target_variance,
    target_achievement_percentage
)
SELECT
    s.store_id,
    t.year_number,
    t.month_number,
    NVL(sales.actual_sales, 0),
    tgt.sales_target,
    NVL(sales.actual_sales, 0) - tgt.sales_target,
    ROUND(
        NVL(sales.actual_sales, 0) * 100.0 / NULLIF(tgt.sales_target, 0),
        2
    )
FROM dwh_owner.FACT_SALES_TARGET tgt
JOIN dwh_owner.DIM_STORE s
    ON s.store_key = tgt.store_key
JOIN dwh_owner.DIM_DATE t
    ON t.date_key = tgt.month_date_key
LEFT JOIN (
    SELECT
        f.store_key,
        d.year_number,
        d.month_number,
        SUM(f.net_amount) AS actual_sales
    FROM dwh_owner.FACT_SALES f
    JOIN dwh_owner.DIM_DATE d
        ON d.date_key = f.date_key
    GROUP BY
        f.store_key,
        d.year_number,
        d.month_number
) sales
    ON sales.store_key = tgt.store_key
   AND sales.year_number = t.year_number
   AND sales.month_number = t.month_number;

COMMIT;