CREATE TABLE dwh_owner.DIM_DATE (
    date_key NUMBER PRIMARY KEY,
    full_date DATE,
    day_number NUMBER(2),
    day_name VARCHAR2(20),
    week_number NUMBER(2),
    month_number NUMBER(2),
    month_name VARCHAR2(20),
    quarter_number NUMBER(1),
    year_number NUMBER(4),
    is_weekend CHAR(1),
    is_holiday CHAR(1)
);