TRUNCATE TABLE mart_owner.DAILY_SALES;

INSERT INTO mart_owner.DAILY_SALES (
    sales_date,
    store_id,
    store_name,
    channel_code,
    gross_sales,
    net_sales,
    profit,
    order_count,
    customer_count,
    units_sold
)
SELECT
    d.full_date,
    s.store_id,
    s.store_name,
    ch.channel_code,
    SUM(f.gross_amount),
    SUM(f.net_amount),
    SUM(f.profit_amount),
    COUNT(DISTINCT f.order_id),
    COUNT(DISTINCT f.customer_key),
    SUM(f.quantity)
FROM dwh_owner.FACT_SALES f
JOIN dwh_owner.DIM_DATE d
    ON d.date_key = f.date_key
JOIN dwh_owner.DIM_STORE s
    ON s.store_key = f.store_key
JOIN dwh_owner.DIM_SALES_CHANNEL ch
    ON ch.channel_key = f.channel_key
GROUP BY
    d.full_date,
    s.store_id,
    s.store_name,
    ch.channel_code;

COMMIT;