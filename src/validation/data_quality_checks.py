"""
Runs data quality checks across RAW, STG and DWH layers, recording
results into AUDIT.DATA_QUALITY_RESULT.

Usage:
    python src/validation/data_quality_checks.py
"""

import os
import uuid

import oracledb
from dotenv import load_dotenv

load_dotenv()

DSN = f"{os.getenv('ORACLE_HOST')}:{os.getenv('ORACLE_PORT')}/{os.getenv('ORACLE_SERVICE_NAME')}"


def connect(user, password):
    return oracledb.connect(user=user, password=password, dsn=DSN)


RULES = [
    {
        "table_name": "RAW.CUSTOMERS",
        "rule_name": "customer_id_not_null",
        "checked_sql": "SELECT COUNT(*) FROM raw_owner.CUSTOMERS",
        "failed_sql": "SELECT COUNT(*) FROM raw_owner.CUSTOMERS WHERE customer_id IS NULL",
    },
    {
        "table_name": "RAW.CUSTOMERS",
        "rule_name": "email_valid_format",
        "checked_sql": "SELECT COUNT(*) FROM raw_owner.CUSTOMERS WHERE customer_id IS NOT NULL",
        "failed_sql": r"""
            SELECT COUNT(*) FROM raw_owner.CUSTOMERS
            WHERE customer_id IS NOT NULL
              AND (email IS NULL OR NOT REGEXP_LIKE(email, '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'))
        """,
    },
    {
        "table_name": "DWH.DIM_CUSTOMER",
        "rule_name": "one_current_version_per_customer",
        "checked_sql": "SELECT COUNT(DISTINCT customer_id) FROM dwh_owner.DIM_CUSTOMER",
        "failed_sql": """
            SELECT COUNT(*) FROM (
                SELECT customer_id FROM dwh_owner.DIM_CUSTOMER
                WHERE is_current = 1
                GROUP BY customer_id HAVING COUNT(*) > 1
            )
        """,
    },
    {
        "table_name": "DWH.DIM_CUSTOMER",
        "rule_name": "effective_to_gte_effective_from",
        "checked_sql": "SELECT COUNT(*) FROM dwh_owner.DIM_CUSTOMER WHERE effective_to IS NOT NULL",
        "failed_sql": "SELECT COUNT(*) FROM dwh_owner.DIM_CUSTOMER WHERE effective_to IS NOT NULL AND effective_to < effective_from",
    },
    {
        "table_name": "RAW.PRODUCTS",
        "rule_name": "list_price_non_negative",
        "checked_sql": "SELECT COUNT(*) FROM raw_owner.PRODUCTS",
        "failed_sql": "SELECT COUNT(*) FROM raw_owner.PRODUCTS WHERE TO_NUMBER(list_price) < 0",
    },
    {
        "table_name": "RAW.PRODUCTS",
        "rule_name": "unit_cost_non_negative",
        "checked_sql": "SELECT COUNT(*) FROM raw_owner.PRODUCTS",
        "failed_sql": "SELECT COUNT(*) FROM raw_owner.PRODUCTS WHERE TO_NUMBER(unit_cost) < 0",
    },
    {
        "table_name": "RAW.PRODUCTS",
        "rule_name": "category_not_null",
        "checked_sql": "SELECT COUNT(*) FROM raw_owner.PRODUCTS",
        "failed_sql": "SELECT COUNT(*) FROM raw_owner.PRODUCTS WHERE category IS NULL",
    },
    {
        "table_name": "DWH.DIM_PRODUCT",
        "rule_name": "product_business_key_unique",
        "checked_sql": "SELECT COUNT(DISTINCT product_id) FROM dwh_owner.DIM_PRODUCT WHERE is_current = 1",
        "failed_sql": """
            SELECT COUNT(*) FROM (
                SELECT product_id FROM dwh_owner.DIM_PRODUCT
                WHERE is_current = 1
                GROUP BY product_id HAVING COUNT(*) > 1
            )
        """,
    },
    {
        "table_name": "RAW.ORDER_ITEMS",
        "rule_name": "quantity_positive",
        "checked_sql": "SELECT COUNT(*) FROM raw_owner.ORDER_ITEMS",
        "failed_sql": "SELECT COUNT(*) FROM raw_owner.ORDER_ITEMS WHERE TO_NUMBER(quantity) <= 0",
    },
    {
        "table_name": "DWH.FACT_SALES",
        "rule_name": "net_amount_non_negative",
        "checked_sql": "SELECT COUNT(*) FROM dwh_owner.FACT_SALES",
        "failed_sql": "SELECT COUNT(*) FROM dwh_owner.FACT_SALES WHERE net_amount < 0",
    },
    {
        "table_name": "RAW.ORDERS",
        "rule_name": "order_date_not_in_future",
        "checked_sql": "SELECT COUNT(*) FROM raw_owner.ORDERS",
        "failed_sql": "SELECT COUNT(*) FROM raw_owner.ORDERS WHERE TO_DATE(order_date, 'YYYY-MM-DD') > TRUNC(SYSDATE)",
    },
    {
        "table_name": "DWH.FACT_SALES",
        "rule_name": "order_item_not_duplicated",
        "checked_sql": "SELECT COUNT(DISTINCT order_item_id) FROM dwh_owner.FACT_SALES",
        "failed_sql": """
            SELECT COUNT(*) FROM (
                SELECT order_item_id FROM dwh_owner.FACT_SALES
                GROUP BY order_item_id HAVING COUNT(*) > 1
            )
        """,
    },
]


def run_checks(batch_id: str):
    conn = connect("audit_owner", os.getenv("ORACLE_AUDIT_PASSWORD", "AuditPass2026"))
    results = []

    try:
        cur = conn.cursor()
        for rule in RULES:
            cur.execute(rule["checked_sql"])
            checked = cur.fetchone()[0] or 0

            cur.execute(rule["failed_sql"])
            failed = cur.fetchone()[0] or 0

            pct = round((failed / checked) * 100, 2) if checked else 0.0
            status = "PASS" if failed == 0 else "FAIL"

            results.append((rule["table_name"], rule["rule_name"], checked, failed, pct, status))

        for table_name, rule_name, checked, failed, pct, status in results:
            cur.execute(
                """
                INSERT INTO DATA_QUALITY_RESULT
                    (batch_id, table_name, rule_name, records_checked,
                     records_failed, failure_percentage, status)
                VALUES
                    (:batch_id, :table_name, :rule_name, :checked, :failed, :pct, :status)
                """,
                batch_id=batch_id, table_name=table_name, rule_name=rule_name,
                checked=checked, failed=failed, pct=pct, status=status,
            )
        conn.commit()
    finally:
        conn.close()

    print(f"Ran {len(results)} data quality checks (batch_id={batch_id})\n")
    for table_name, rule_name, checked, failed, pct, status in results:
        print(f"  [{status}] {table_name}.{rule_name}: {failed}/{checked} failed ({pct}%)")

    return results


if __name__ == "__main__":
    run_checks(str(uuid.uuid4()))