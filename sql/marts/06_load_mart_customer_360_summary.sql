TRUNCATE TABLE mart_owner.CUSTOMER_360_SUMMARY;

INSERT INTO mart_owner.CUSTOMER_360_SUMMARY (
    customer_id,
    lifetime_value,
    total_orders,
    total_spent,
    average_order_value,
    first_order_date,
    last_order_date,
    preferred_category,
    return_rate
)
WITH customer_base AS (
    SELECT
        c.customer_id,
        SUM(f.net_amount) AS total_spent,
        COUNT(DISTINCT f.order_id) AS total_orders,
        MIN(d.full_date) AS first_order_date,
        MAX(d.full_date) AS last_order_date,
        SUM(f.quantity) AS total_units
    FROM dwh_owner.FACT_SALES f
    JOIN dwh_owner.DIM_CUSTOMER c
        ON c.customer_key = f.customer_key
    JOIN dwh_owner.DIM_DATE d
        ON d.date_key = f.date_key
    GROUP BY
        c.customer_id
),
category_rank AS (
    SELECT
        c.customer_id,
        p.category,
        ROW_NUMBER() OVER (
            PARTITION BY c.customer_id
            ORDER BY SUM(f.net_amount) DESC
        ) AS rn
    FROM dwh_owner.FACT_SALES f
    JOIN dwh_owner.DIM_CUSTOMER c
        ON c.customer_key = f.customer_key
    JOIN dwh_owner.DIM_PRODUCT p
        ON p.product_key = f.product_key
    GROUP BY
        c.customer_id,
        p.category
),
customer_returns AS (
    SELECT
        c.customer_id,
        SUM(fr.return_quantity) AS total_returned
    FROM dwh_owner.FACT_RETURNS fr
    JOIN dwh_owner.DIM_CUSTOMER c
        ON c.customer_key = fr.customer_key
    GROUP BY
        c.customer_id
)
SELECT
    b.customer_id,
    b.total_spent AS lifetime_value,
    b.total_orders,
    b.total_spent,
    ROUND(b.total_spent / NULLIF(b.total_orders, 0), 2) AS average_order_value,
    b.first_order_date,
    b.last_order_date,
    cr.category,
    ROUND(
        NVL(ret.total_returned, 0) * 100.0 / NULLIF(b.total_units, 0),
        2
    ) AS return_rate
FROM customer_base b
LEFT JOIN category_rank cr
    ON cr.customer_id = b.customer_id
   AND cr.rn = 1
LEFT JOIN customer_returns ret
    ON ret.customer_id = b.customer_id;

COMMIT;