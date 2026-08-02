"""
Loads generated sample data files into Oracle RAW schema tables.
Refactored into per-source callables so each can run as an independent
Airflow task. Uses AUDIT.ETL_WATERMARK for incremental extraction on
sources with an updated_at field (customers, products, orders).

CLI usage (manual full run):
    python src/ingestion/load_raw.py
"""

import csv
import hashlib
import json
import os
import uuid
from datetime import datetime
from pathlib import Path

import oracledb
from dotenv import load_dotenv

load_dotenv()

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "sample"
PIPELINE_NAME = "ingest_sales_sources"

DSN = f"{os.getenv('ORACLE_HOST')}:{os.getenv('ORACLE_PORT')}/{os.getenv('ORACLE_SERVICE_NAME')}"


def record_hash(record: dict) -> str:
    payload = json.dumps(record, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def connect(user: str, password: str):
    return oracledb.connect(user=user, password=password, dsn=DSN)


def _raw_connect():
    return connect("raw_owner", os.getenv("ORACLE_RAW_PASSWORD", "RawPass2026"))


def get_watermark(conn, source_name: str):
    cur = conn.cursor()
    cur.execute(
        """
        SELECT last_successful_timestamp
        FROM audit_owner.ETL_WATERMARK
        WHERE pipeline_name = :pipeline_name AND source_name = :source_name
        """,
        pipeline_name=PIPELINE_NAME,
        source_name=source_name,
    )
    row = cur.fetchone()
    return row[0] if row else None


def set_watermark(conn, source_name: str, ts: datetime):
    cur = conn.cursor()
    cur.execute(
        """
        MERGE INTO audit_owner.ETL_WATERMARK tgt
        USING (SELECT :pipeline_name AS pipeline_name, :source_name AS source_name FROM dual) src
        ON (tgt.pipeline_name = src.pipeline_name AND tgt.source_name = src.source_name)
        WHEN MATCHED THEN UPDATE SET
            last_successful_timestamp = :ts, updated_at = SYSTIMESTAMP
        WHEN NOT MATCHED THEN INSERT (pipeline_name, source_name, last_successful_timestamp, updated_at)
        VALUES (:pipeline_name, :source_name, :ts, SYSTIMESTAMP)
        """,
        pipeline_name=PIPELINE_NAME,
        source_name=source_name,
        ts=ts,
    )
    conn.commit()


def parse_updated_at(value: str) -> datetime:
    return datetime.fromisoformat(value).replace(microsecond=0)


def filter_incremental(records, watermark):
    if watermark is None:
        return records
    return [r for r in records if parse_updated_at(r["updated_at"]) > watermark]


def load_json(conn, filename, table, columns, source_system, batch_id, incremental=False):
    with open(DATA_DIR / filename, "r", encoding="utf-8") as f:
        records = json.load(f)

    watermark = get_watermark(conn, source_system) if incremental else None
    if incremental:
        records = filter_incremental(records, watermark)

    if not records:
        print(f"{filename} -> 0 new rows (watermark: {watermark})")
        return 0

    cols = columns + ["source_file", "source_system", "batch_id", "record_hash"]
    placeholders = ", ".join(f":{i+1}" for i in range(len(cols)))
    sql = f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({placeholders})"

    cur = conn.cursor()
    rows = []
    max_updated_at = watermark
    for r in records:
        values = [str(r.get(c)) if r.get(c) is not None else None for c in columns]
        values += [filename, source_system, batch_id, record_hash(r)]
        rows.append(values)
        if incremental:
            ts = parse_updated_at(r["updated_at"])
            if max_updated_at is None or ts > max_updated_at:
                max_updated_at = ts

    cur.executemany(sql, rows)
    conn.commit()
    print(f"{filename} -> {len(rows)} new rows loaded into {table}")

    if incremental and max_updated_at:
        set_watermark(conn, source_system, max_updated_at)

    return len(rows)


def load_csv(conn, filename, table, columns, source_system, batch_id, include_hash=True, incremental=False):
    with open(DATA_DIR / filename, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        records = list(reader)

    watermark = get_watermark(conn, source_system) if incremental else None
    if incremental:
        records = filter_incremental(records, watermark)

    if not records:
        print(f"{filename} -> 0 new rows (watermark: {watermark})")
        return 0

    extra_cols = ["source_file", "source_system", "batch_id"]
    if include_hash:
        extra_cols.append("record_hash")
    cols = columns + extra_cols

    placeholders = ", ".join(f":{i+1}" for i in range(len(cols)))
    sql = f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({placeholders})"

    cur = conn.cursor()
    rows = []
    max_updated_at = watermark
    for r in records:
        values = [r.get(c) if r.get(c) != "" else None for c in columns]
        values += [filename, source_system, batch_id]
        if include_hash:
            values.append(record_hash(r))
        rows.append(values)
        if incremental:
            ts = parse_updated_at(r["updated_at"])
            if max_updated_at is None or ts > max_updated_at:
                max_updated_at = ts

    cur.executemany(sql, rows)
    conn.commit()
    print(f"{filename} -> {len(rows)} new rows loaded into {table}")

    if incremental and max_updated_at:
        set_watermark(conn, source_system, max_updated_at)

    return len(rows)


def extract_customers(batch_id: str) -> int:
    conn = _raw_connect()
    try:
        return load_json(
            conn, "customers.json", "CUSTOMERS",
            ["customer_id", "first_name", "last_name", "email", "phone", "city",
             "country", "registration_date", "customer_segment", "updated_at"],
            "customers_json", batch_id, incremental=True,
        )
    finally:
        conn.close()


def extract_products(batch_id: str) -> int:
    conn = _raw_connect()
    try:
        return load_csv(
            conn, "products.csv", "PRODUCTS",
            ["product_id", "product_name", "category", "subcategory", "brand",
             "supplier_id", "unit_cost", "list_price", "active_flag", "updated_at"],
            "products_csv", batch_id, incremental=True,
        )
    finally:
        conn.close()


def extract_orders(batch_id: str) -> int:
    conn = _raw_connect()
    try:
        return load_json(
            conn, "orders.json", "ORDERS",
            ["order_id", "customer_id", "store_id", "order_date", "order_status",
             "currency", "total_amount", "created_at", "updated_at"],
            "orders_api", batch_id, incremental=True,
        )
    finally:
        conn.close()


def extract_order_items(batch_id: str) -> int:
    conn = _raw_connect()
    try:
        return load_csv(
            conn, "order_items.csv", "ORDER_ITEMS",
            ["order_item_id", "order_id", "product_id", "quantity", "unit_price",
             "discount_amount", "tax_amount"],
            "order_items_csv", batch_id,
        )
    finally:
        conn.close()


def extract_returns(batch_id: str) -> int:
    conn = _raw_connect()
    try:
        return load_csv(
            conn, "returns.csv", "RETURNS",
            ["return_id", "order_item_id", "return_date", "return_reason",
             "return_quantity", "refund_amount"],
            "returns_csv", batch_id,
        )
    finally:
        conn.close()


def extract_stores(batch_id: str) -> int:
    conn = _raw_connect()
    try:
        return load_csv(
            conn, "stores.csv", "STORES",
            ["store_id", "store_name", "store_type", "city", "country", "region", "opening_date"],
            "stores_csv", batch_id, include_hash=False,
        )
    finally:
        conn.close()


def extract_sales_targets(batch_id: str) -> int:
    conn = _raw_connect()
    try:
        return load_csv(
            conn, "sales_targets.csv", "SALES_TARGETS",
            ["store_id", "year", "month", "sales_target", "profit_target"],
            "sales_targets_csv", batch_id, include_hash=False,
        )
    finally:
        conn.close()


def record_etl_run(batch_id, start_time, end_time, status, rows_extracted, error_message=None):
    conn = connect("audit_owner", os.getenv("ORACLE_AUDIT_PASSWORD", "AuditPass2026"))
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO ETL_RUN
                (pipeline_name, batch_id, start_time, end_time, status,
                 rows_extracted, rows_loaded, rows_rejected, error_message)
            VALUES
                (:pipeline_name, :batch_id, :start_time, :end_time, :status,
                 :rows_extracted, :rows_extracted, 0, :error_message)
            """,
            pipeline_name=PIPELINE_NAME,
            batch_id=batch_id,
            start_time=start_time,
            end_time=end_time,
            status=status,
            rows_extracted=rows_extracted,
            error_message=error_message,
        )
        conn.commit()
    finally:
        conn.close()


def main():
    batch_id = str(uuid.uuid4())
    print(f"Batch ID: {batch_id}\n")

    total = 0
    total += extract_customers(batch_id)
    total += extract_products(batch_id)
    total += extract_orders(batch_id)
    total += extract_stores(batch_id)
    total += extract_order_items(batch_id)
    total += extract_returns(batch_id)
    total += extract_sales_targets(batch_id)

    print(f"\nDone. Total new rows loaded: {total}")


if __name__ == "__main__":
    main()