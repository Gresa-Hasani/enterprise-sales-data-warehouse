"""
NovaRetail Analytics - synthetic data generator.

Generates small-volume sample data (for pipeline testing) into data/sample/.
Intentional data quality issues are injected on purpose so downstream
validation/staging logic has something to catch.

Usage:
    python data/generators/generate_all.py
"""

import csv
import json
import random
from datetime import datetime, timedelta
from pathlib import Path

from faker import Faker

fake = Faker()
random.seed(42)
Faker.seed(42)

OUT_DIR = Path(__file__).resolve().parent.parent / "sample"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ---- volume knobs (small for first end-to-end test run) ----
N_CUSTOMERS = 1_000
N_PRODUCTS = 200
N_STORES = 20
N_ORDERS = 5_000
N_RETURNS = 250

CURRENCIES = ["USD", "EUR", "GBP"]
INVALID_CURRENCIES = ["XXX", "ZZZ", "???"]
SEGMENTS = ["Regular", "VIP", "New", "Inactive"]
CATEGORIES = {
    "Electronics": ["Phones", "Laptops", "Accessories"],
    "Clothing": ["Men", "Women", "Kids"],
    "Home": ["Kitchen", "Furniture", "Decor"],
    "Sports": ["Fitness", "Outdoor", "Team Sports"],
}
ORDER_STATUSES = ["PLACED", "SHIPPED", "DELIVERED", "CANCELLED", "RETURNED"]
CHANNELS = ["WEB", "MOBILE", "STORE", "PARTNER"]


def random_date(start_year=2021, end_year=2026):
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 12, 31)
    delta = end - start
    return start + timedelta(days=random.randint(0, delta.days))


# ---------------------------------------------------------------------------
# CUSTOMERS (JSON) - includes duplicates and invalid emails on purpose
# ---------------------------------------------------------------------------
def generate_customers():
    customers = []
    for i in range(1, N_CUSTOMERS + 1):
        customer_id = f"CUST{i:06d}"
        email = fake.email()

        # inject invalid email ~2% of the time
        if random.random() < 0.02:
            email = email.replace("@", "_at_")

        customers.append({
            "customer_id": customer_id,
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "email": email,
            "phone": fake.phone_number(),
            "city": fake.city(),
            "country": fake.country(),
            "registration_date": random_date(2018, 2026).strftime("%Y-%m-%d"),
            "customer_segment": random.choice(SEGMENTS),
            "updated_at": datetime.now().isoformat(),
        })

    # inject duplicate customers ~1%
    n_dupes = max(1, N_CUSTOMERS // 100)
    for _ in range(n_dupes):
        customers.append(random.choice(customers[:N_CUSTOMERS]).copy())

    with open(OUT_DIR / "customers.json", "w", encoding="utf-8") as f:
        json.dump(customers, f, indent=2)

    print(f"customers.json -> {len(customers)} records ({n_dupes} intentional duplicates)")
    return [c["customer_id"] for c in customers[:N_CUSTOMERS]]


# ---------------------------------------------------------------------------
# PRODUCTS (CSV)
# ---------------------------------------------------------------------------
def generate_products():
    rows = []
    for i in range(1, N_PRODUCTS + 1):
        product_id = f"PROD{i:05d}"
        category = random.choice(list(CATEGORIES.keys()))
        subcategory = random.choice(CATEGORIES[category])
        unit_cost = round(random.uniform(2, 300), 2)
        list_price = round(unit_cost * random.uniform(1.2, 2.5), 2)

        # inject negative price ~1%
        if random.random() < 0.01:
            list_price = -abs(list_price)

        rows.append({
            "product_id": product_id,
            "product_name": fake.catch_phrase(),
            "category": category,
            "subcategory": subcategory,
            "brand": fake.company(),
            "supplier_id": f"SUP{random.randint(1, 50):04d}",
            "unit_cost": unit_cost,
            "list_price": list_price,
            "active_flag": random.choice(["Y", "Y", "Y", "N"]),
            "updated_at": datetime.now().isoformat(),
        })

    with open(OUT_DIR / "products.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"products.csv -> {len(rows)} records")
    return [r["product_id"] for r in rows]


# ---------------------------------------------------------------------------
# STORES (CSV)
# ---------------------------------------------------------------------------
def generate_stores():
    rows = []
    for i in range(1, N_STORES + 1):
        rows.append({
            "store_id": f"STORE{i:04d}",
            "store_name": f"{fake.city()} Store",
            "store_type": random.choice(["FLAGSHIP", "STANDARD", "OUTLET"]),
            "city": fake.city(),
            "country": fake.country(),
            "region": fake.state(),
            "opening_date": random_date(2015, 2024).strftime("%Y-%m-%d"),
        })

    with open(OUT_DIR / "stores.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"stores.csv -> {len(rows)} records")
    return [r["store_id"] for r in rows]


# ---------------------------------------------------------------------------
# ORDERS (simulating the "Orders API" source as JSON) + ORDER_ITEMS (CSV)
# ---------------------------------------------------------------------------
def generate_orders_and_items(customer_ids, product_ids, store_ids):
    orders = []
    order_items = []
    order_item_seq = 1

    for i in range(1, N_ORDERS + 1):
        order_id = f"ORD{i:07d}"
        order_date = random_date(2021, 2026)
        currency = random.choice(CURRENCIES)

        # inject unknown currency ~1%
        if random.random() < 0.01:
            currency = random.choice(INVALID_CURRENCIES)

        # inject future order_date ~1%
        if random.random() < 0.01:
            order_date = datetime.now() + timedelta(days=random.randint(1, 60))

        created_at = order_date
        updated_at = created_at + timedelta(days=random.randint(0, 5))

        n_items = random.randint(1, 5)
        order_total = 0.0

        for _ in range(n_items):
            product_id = random.choice(product_ids)

            # inject non-existent product_id ~1%
            if random.random() < 0.01:
                product_id = f"PRODXXXXX{random.randint(1,999)}"

            quantity = random.randint(1, 5)
            unit_price = round(random.uniform(5, 500), 2)

            # inject negative price ~1%
            if random.random() < 0.01:
                unit_price = -abs(unit_price)

            discount_amount = round(unit_price * random.uniform(0, 0.2), 2)
            tax_amount = round(unit_price * 0.1, 2)

            order_items.append({
                "order_item_id": f"OI{order_item_seq:08d}",
                "order_id": order_id,
                "product_id": product_id,
                "quantity": quantity,
                "unit_price": unit_price,
                "discount_amount": discount_amount,
                "tax_amount": tax_amount,
            })
            order_item_seq += 1
            order_total += quantity * unit_price

        customer_id = random.choice(customer_ids)
        # inject null customer_id ~1%
        if random.random() < 0.01:
            customer_id = None

        orders.append({
            "order_id": order_id,
            "customer_id": customer_id,
            "store_id": random.choice(store_ids),
            "order_date": order_date.strftime("%Y-%m-%d"),
            "order_status": random.choice(ORDER_STATUSES),
            "currency": currency,
            "total_amount": round(order_total, 2),
            "created_at": created_at.isoformat(),
            "updated_at": updated_at.isoformat(),
        })

    # inject duplicate orders ~0.5%
    n_dupes = max(1, N_ORDERS // 200)
    for _ in range(n_dupes):
        orders.append(random.choice(orders[:N_ORDERS]).copy())

    with open(OUT_DIR / "orders.json", "w", encoding="utf-8") as f:
        json.dump(orders, f, indent=2)
    print(f"orders.json -> {len(orders)} records ({n_dupes} intentional duplicate orders)")

    with open(OUT_DIR / "order_items.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=order_items[0].keys())
        writer.writeheader()
        writer.writerows(order_items)
    print(f"order_items.csv -> {len(order_items)} records")

    return [oi["order_item_id"] for oi in order_items]


# ---------------------------------------------------------------------------
# RETURNS (CSV)
# ---------------------------------------------------------------------------
def generate_returns(order_item_ids):
    rows = []
    for i in range(1, N_RETURNS + 1):
        return_date = random_date(2021, 2026)
        refund_amount = round(random.uniform(5, 300), 2)

        rows.append({
            "return_id": f"RET{i:06d}",
            "order_item_id": random.choice(order_item_ids),
            "return_date": return_date.strftime("%Y-%m-%d"),
            "return_reason": random.choice(
                ["DAMAGED", "WRONG_ITEM", "NOT_AS_DESCRIBED", "CHANGED_MIND"]
            ),
            "return_quantity": random.randint(1, 2),
            "refund_amount": refund_amount,
        })

    with open(OUT_DIR / "returns.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"returns.csv -> {len(rows)} records")


# ---------------------------------------------------------------------------
# SALES TARGETS (CSV)
# ---------------------------------------------------------------------------
def generate_sales_targets(store_ids):
    rows = []
    for store_id in store_ids:
        for year in range(2023, 2027):
            for month in range(1, 13):
                rows.append({
                    "store_id": store_id,
                    "year": year,
                    "month": month,
                    "sales_target": round(random.uniform(20000, 100000), 2),
                    "profit_target": round(random.uniform(4000, 25000), 2),
                })

    with open(OUT_DIR / "sales_targets.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"sales_targets.csv -> {len(rows)} records")


def main():
    print(f"Writing sample data to: {OUT_DIR}\n")
    customer_ids = generate_customers()
    product_ids = generate_products()
    store_ids = generate_stores()
    order_item_ids = generate_orders_and_items(customer_ids, product_ids, store_ids)
    generate_returns(order_item_ids)
    generate_sales_targets(store_ids)
    print("\nDone.")


if __name__ == "__main__":
    main()