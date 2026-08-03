CREATE MATERIALIZED VIEW dwh_owner.MV_MONTHLY_SALES_SUMMARY
BUILD IMMEDIATE
REFRESH COMPLETE ON DEMAND
AS
SELECT
    d.year_number,
    d.month_number,
    s.store_id,
    s.store_name,
    SUM(f.net_amount) AS revenue,
    SUM(f.profit_amount) AS profit,
    SUM(f.quantity) AS units_sold,
    COUNT(DISTINCT f.order_id) AS order_count
FROM dwh_owner.FACT_SALES f
JOIN dwh_owner.DIM_DATE d
    ON d.date_key = f.date_key
JOIN dwh_owner.DIM_STORE s
    ON s.store_key = f.store_key
GROUP BY
    d.year_number,
    d.month_number,
    s.store_id,
    s.store_name;