"""
Loads generated sample data files into Oracle RAW schema tables.

Usage:
    python src/ingestion/load_raw.py
"""

import csv
import hashlib
import json
import os
import uuid
from pathlib import Path

import oracledb
from dotenv import load_dotenv

load_dotenv()

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "sample"
BATCH_ID = str(uuid.uuid4())

DSN = f"{os.getenv('ORACLE_HOST')}:{os.getenv('ORACLE_PORT')}/{os.getenv('ORACLE_SERVICE_NAME')}"


def record_hash(record: dict) -> str:
    payload = json.dumps(record, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def connect(user: str, password: str):
    return oracledb.connect(user=user, password=password, dsn=DSN)


def load_json(conn, filename, table, columns, source_system, include_hash=True):
    with open(DATA_DIR / filename, "r", encoding="utf-8") as f:
        records = json.load(f)

    extra_cols = ["source_file", "source_system", "batch_id"]
    if include_hash:
        extra_cols.append("record_hash")
    cols = columns + extra_cols

    placeholders = ", ".join(f":{i+1}" for i in range(len(cols)))
    sql = f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({placeholders})"

    cur = conn.cursor()
    rows = []
    for r in records:
        values = [str(r.get(c)) if r.get(c) is not None else None for c in columns]
        values += [filename, source_system, BATCH_ID]
        if include_hash:
            values.append(record_hash(r))
        rows.append(values)

    cur.executemany(sql, rows)
    conn.commit()
    print(f"{filename} -> {len(rows)} rows loaded into {table}")


def load_csv(conn, filename, table, columns, source_system, include_hash=True):
    with open(DATA_DIR / filename, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        records = list(reader)

    extra_cols = ["source_file", "source_system", "batch_id"]
    if include_hash:
        extra_cols.append("record_hash")
    cols = columns + extra_cols

    placeholders = ", ".join(f":{i+1}" for i in range(len(cols)))
    sql = f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({placeholders})"

    cur = conn.cursor()
    rows = []
    for r in records:
        values = [r.get(c) if r.get(c) != "" else None for c in columns]
        values += [filename, source_system, BATCH_ID]
        if include_hash:
            values.append(record_hash(r))
        rows.append(values)

    cur.executemany(sql, rows)
    conn.commit()
    print(f"{filename} -> {len(rows)} rows loaded into {table}")


def main():
    print(f"Batch ID: {BATCH_ID}\n")
    conn = connect("raw_owner", os.getenv("ORACLE_RAW_PASSWORD", "RawPass2026"))

    load_json(
        conn, "customers.json", "CUSTOMERS",
        ["customer_id", "first_name", "last_name", "email", "phone", "city",
         "country", "registration_date", "customer_segment", "updated_at"],
        "customers_json",
    )

    load_csv(
        conn, "products.csv", "PRODUCTS",
        ["product_id", "product_name", "category", "subcategory", "brand",
         "supplier_id", "unit_cost", "list_price", "active_flag", "updated_at"],
        "products_csv",
    )

    load_csv(
        conn, "stores.csv", "STORES",
        ["store_id", "store_name", "store_type", "city", "country", "region", "opening_date"],
        "stores_csv",
        include_hash=False,
    )

    load_json(
        conn, "orders.json", "ORDERS",
        ["order_id", "customer_id", "store_id", "order_date", "order_status",
         "currency", "total_amount", "created_at", "updated_at"],
        "orders_api",
    )

    load_csv(
        conn, "order_items.csv", "ORDER_ITEMS",
        ["order_item_id", "order_id", "product_id", "quantity", "unit_price",
         "discount_amount", "tax_amount"],
        "order_items_csv",
    )

    load_csv(
        conn, "returns.csv", "RETURNS",
        ["return_id", "order_item_id", "return_date", "return_reason",
         "return_quantity", "refund_amount"],
        "returns_csv",
    )

    load_csv(
        conn, "sales_targets.csv", "SALES_TARGETS",
        ["store_id", "year", "month", "sales_target", "profit_target"],
        "sales_targets_csv",
        include_hash=False,
    )

    conn.close()
    print("\nDone.")


if __name__ == "__main__":
    main()