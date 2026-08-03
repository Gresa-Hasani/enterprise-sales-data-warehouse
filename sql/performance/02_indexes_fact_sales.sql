CREATE INDEX idx_fact_sales_customer_date ON dwh_owner.FACT_SALES (customer_key, date_key) LOCAL;
CREATE INDEX idx_fact_sales_product_date ON dwh_owner.FACT_SALES (product_key, date_key) LOCAL;
CREATE INDEX idx_fact_sales_store_date ON dwh_owner.FACT_SALES (store_key, date_key) LOCAL;