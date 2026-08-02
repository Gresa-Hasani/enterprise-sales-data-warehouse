INSERT INTO dwh_owner.DIM_DATE
SELECT
    TO_NUMBER(TO_CHAR(d, 'YYYYMMDD')) AS date_key,
    d AS full_date,
    TO_NUMBER(TO_CHAR(d, 'DD')) AS day_number,
    TRIM(TO_CHAR(d, 'DAY')) AS day_name,
    TO_NUMBER(TO_CHAR(d, 'IW')) AS week_number,
    TO_NUMBER(TO_CHAR(d, 'MM')) AS month_number,
    TRIM(TO_CHAR(d, 'MONTH')) AS month_name,
    TO_NUMBER(TO_CHAR(d, 'Q')) AS quarter_number,
    TO_NUMBER(TO_CHAR(d, 'YYYY')) AS year_number,
    CASE
        WHEN TO_CHAR(d, 'D') IN ('1','7') THEN 'Y'
        ELSE 'N'
    END AS is_weekend,
    'N' AS is_holiday
FROM (
    SELECT DATE '2018-01-01' + LEVEL - 1 AS d
    FROM dual
    CONNECT BY LEVEL <= (DATE '2027-12-31' - DATE '2018-01-01' + 1)
);
COMMIT;