"""
Integration tests verifying data flows correctly RAW -> STG -> DWH -> MART.
Require a running Oracle instance (docker compose up -d). Automatically
skipped if the database is unreachable (e.g. in CI without Oracle).
"""

import os

import oracledb
import pytest
from dotenv import load_dotenv

load_dotenv()

DSN = f"{os.getenv('ORACLE_HOST', 'localhost')}:{os.getenv('ORACLE_PORT', '1521')}/{os.getenv('ORACLE_SERVICE_NAME', 'XEPDB1')}"


def _connect(user, password):
    return oracledb.connect(user=user, password=password, dsn=DSN)


def _oracle_available():
    try:
        conn = _connect("raw_owner", os.getenv("ORACLE_RAW_PASSWORD", "RawPass2026"))
        conn.close()
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not _oracle_available(), reason="Oracle is not reachable")


class TestStagingReconciliation:
    def test_customers_clean_has_no_more_rows_than_raw(self):
        raw_conn = _connect("raw_owner", os.getenv("ORACLE_RAW_PASSWORD", "RawPass2026"))
        stg_conn = _connect("stg_owner", os.getenv("ORACLE_STG_PASSWORD", "StgPass2026"))

        raw_count = raw_conn.cursor().execute("SELECT COUNT(*) FROM CUSTOMERS").fetchone()[0]
        stg_count = stg_conn.cursor().execute("SELECT COUNT(*) FROM CUSTOMERS_CLEAN").fetchone()[0]

        raw_conn.close()
        stg_conn.close()

        assert stg_count <= raw_count

    def test_no_duplicate_customer_ids_in_staging(self):
        conn = _connect("stg_owner", os.getenv("ORACLE_STG_PASSWORD", "StgPass2026"))
        cur = conn.cursor()
        cur.execute(
            "SELECT COUNT(*) FROM (SELECT customer_id FROM CUSTOMERS_CLEAN GROUP BY customer_id HAVING COUNT(*) > 1)"
        )
        duplicate_count = cur.fetchone()[0]
        conn.close()
        assert duplicate_count == 0


class TestDimensionInvariants:
    def test_exactly_one_current_version_per_customer(self):
        conn = _connect("dwh_owner", os.getenv("ORACLE_DWH_PASSWORD", "DwhPass2026"))
        cur = conn.cursor()
        cur.execute(
            """
            SELECT COUNT(*) FROM (
                SELECT customer_id FROM DIM_CUSTOMER
                WHERE is_current = 1
                GROUP BY customer_id HAVING COUNT(*) > 1
            )
            """
        )
        violations = cur.fetchone()[0]
        conn.close()
        assert violations == 0

    def test_no_orphan_order_items_in_fact_sales(self):
        conn = _connect("dwh_owner", os.getenv("ORACLE_DWH_PASSWORD", "DwhPass2026"))
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM FACT_SALES WHERE customer_key IS NULL OR product_key IS NULL")
        orphans = cur.fetchone()[0]
        conn.close()
        assert orphans == 0


class TestFactToSourceReconciliation:
    def test_fact_sales_row_count_matches_staging_order_items(self):
        stg_conn = _connect("stg_owner", os.getenv("ORACLE_STG_PASSWORD", "StgPass2026"))
        dwh_conn = _connect("dwh_owner", os.getenv("ORACLE_DWH_PASSWORD", "DwhPass2026"))

        stg_count = stg_conn.cursor().execute("SELECT COUNT(*) FROM ORDER_ITEMS_CLEAN").fetchone()[0]
        fact_count = dwh_conn.cursor().execute("SELECT COUNT(*) FROM FACT_SALES").fetchone()[0]

        stg_conn.close()
        dwh_conn.close()

        # fact count can be <= staging count (some rows may not match a current dim version)
        assert fact_count <= stg_count

    def test_mart_daily_sales_is_populated(self):
        conn = _connect("mart_owner", os.getenv("ORACLE_MART_PASSWORD", "MartPass2026"))
        count = conn.cursor().execute("SELECT COUNT(*) FROM DAILY_SALES").fetchone()[0]
        conn.close()
        assert count > 0