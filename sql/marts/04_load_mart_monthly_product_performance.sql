TRUNCATE TABLE mart_owner.MONTHLY_PRODUCT_PERFORMANCE;

INSERT INTO mart_owner.MONTHLY_PRODUCT_PERFORMANCE (
    year,
    month,
    product_id,
    product_name,
    category,
    revenue,
    profit,
    units_sold,
    units_returned,
    return_rate
)
SELECT
    d.year_number,
    d.month_number,
    p.product_id,
    p.product_name,
    p.category,
    SUM(f.net_amount),
    SUM(f.profit_amount),
    SUM(f.quantity),
    NVL(r.total_returned, 0),
    ROUND(
        NVL(r.total_returned, 0) * 100.0 / NULLIF(SUM(f.quantity), 0),
        2
    )
FROM dwh_owner.FACT_SALES f
JOIN dwh_owner.DIM_DATE d
    ON d.date_key = f.date_key
JOIN dwh_owner.DIM_PRODUCT p
    ON p.product_key = f.product_key
LEFT JOIN (
    SELECT
        rd.year_number AS ret_year,
        rd.month_number AS ret_month,
        rp.product_id AS ret_product_id,
        SUM(fr.return_quantity) AS total_returned
    FROM dwh_owner.FACT_RETURNS fr
    JOIN dwh_owner.DIM_DATE rd
        ON rd.date_key = fr.return_date_key
    JOIN dwh_owner.DIM_PRODUCT rp
        ON rp.product_key = fr.product_key
    GROUP BY
        rd.year_number,
        rd.month_number,
        rp.product_id
) r
    ON r.ret_year = d.year_number
   AND r.ret_month = d.month_number
   AND r.ret_product_id = p.product_id
GROUP BY
    d.year_number,
    d.month_number,
    p.product_id,
    p.product_name,
    p.category,
    r.total_returned;

COMMIT;