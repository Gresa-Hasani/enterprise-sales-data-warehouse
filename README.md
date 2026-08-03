# Enterprise Sales Data Warehouse — NovaRetail Analytics

[![CI](https://github.com/Gresa-Hasani/enterprise-sales-data-warehouse/actions/workflows/ci.yml/badge.svg)](https://github.com/Gresa-Hasani/enterprise-sales-data-warehouse/actions/workflows/ci.yml)

A full, end-to-end Enterprise Data Warehouse built for **NovaRetail Analytics**, a fictional retail company selling online and in physical stores. The project simulates a realistic multi-source retail environment (orders, customers, products, returns, stores, sales targets) and builds a complete pipeline from raw ingestion to BI dashboards, following standard data engineering practices: RAW/STG/DWH/MART layering, SCD Type 2 dimensions, incremental loading, data quality validation, orchestration, performance tuning, and CI/CD.

## Architecture

```
Source Systems (API / CSV / JSON)
        │
        ▼
Python Ingestion (validation, hashing, incremental extraction)
        │
        ▼
Oracle RAW schema (append-only, near-source fidelity)
        │
        ▼
Staging (STG) — cleaning, deduplication, validation, rejected records
        │
        ▼
Data Warehouse (DWH) — star schema: dimensions (SCD Type 2) + fact tables
        │
        ▼
Data Marts (MART) — pre-aggregated tables for BI
        │
        ▼
Power BI Dashboard (4 pages)
```

Orchestrated end-to-end by three Apache Airflow DAGs; monitored via an audit trail (`ETL_RUN`, `ETL_STEP_RUN`, `REJECTED_RECORDS`, `DATA_QUALITY_RESULT`, `ETL_WATERMARK`).

## Tech stack

| Layer | Technology |
|---|---|
| Database | Oracle Database XE 21c (Docker) |
| Ingestion / scripting | Python 3.13, `oracledb` (thin mode), `python-dotenv` |
| Synthetic data | Faker |
| Orchestration | Apache Airflow 2.9 (LocalExecutor + Postgres metadata store, Dockerized) |
| Transformations | SQL / PL-SQL (staging, dimensions, facts, marts) |
| Data quality | Custom Python rule engine + `AUDIT.DATA_QUALITY_RESULT` |
| BI | Power BI Desktop (direct Oracle connection via Instant Client) |
| Testing | pytest (unit + integration) |
| CI/CD | GitHub Actions |
| Environment | Docker Compose |

## Data model

**Schemas**: `RAW_OWNER`, `STG_OWNER`, `DWH_OWNER`, `MART_OWNER`, `AUDIT_OWNER`

**Dimensions** (`DWH_OWNER`): `DIM_DATE`, `DIM_STORE`, `DIM_SALES_CHANNEL`, `DIM_ORDER_STATUS`, `DIM_CUSTOMER` (SCD Type 2), `DIM_PRODUCT` (SCD Type 2)

**Facts** (`DWH_OWNER`): `FACT_SALES` (grain: one row per order item; partitioned by year on `date_key`), `FACT_RETURNS`, `FACT_SALES_TARGET`

**Marts** (`MART_OWNER`): `DAILY_SALES`, `MONTHLY_PRODUCT_PERFORMANCE`, `CUSTOMER_360_SUMMARY`, `STORE_TARGET_PERFORMANCE`

## Project structure

```
enterprise-sales-data-warehouse/
├── airflow/dags/            # 3 Airflow DAGs
├── data/generators/         # Faker-based synthetic data generator
├── docs/                    # performance-results.md and other docs
├── powerbi/screenshots/     # 4-page dashboard screenshots
├── sql/
│   ├── init/                # RAW + AUDIT schema/table DDL (Docker init mount)
│   ├── staging/              # cleaning/validation SQL per entity
│   ├── dimensions/           # dimension DDL + SCD2 load logic
│   ├── facts/                # fact table DDL + load logic
│   ├── marts/                # mart DDL + refresh logic
│   └── performance/          # partitioning, indexes, execution plan benchmarks
├── src/
│   ├── ingestion/            # load_raw.py — per-source extraction + incremental logic
│   ├── validation/           # rules.py (pure functions) + data_quality_checks.py
│   └── utils/                # sql_runner.py — generic .sql file executor for Airflow
├── tests/
│   ├── unit/                 # 26 tests — rules, hashing, incremental filtering
│   └── integration/          # 6 tests — RAW→STG→DWH→MART reconciliation
├── docker-compose.yml        # Oracle XE + Airflow (webserver, scheduler, Postgres)
└── .github/workflows/ci.yml  # GitHub Actions — runs unit tests on push/PR
```

## Getting started

### Prerequisites
- Docker Desktop
- Python 3.11+ (a separate 3.11 venv is recommended if your system default is newer, since Airflow's local tooling lags behind)
- Oracle Instant Client (Basic Package, 64-bit) + Power BI Desktop, only if you want to explore the dashboard yourself

### 1. Environment setup
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # edit passwords as needed
```

### 2. Start Oracle + Airflow
```bash
docker compose up -d
```
Wait for `nova_oracle_xe` to report `DATABASE IS READY TO USE!` in its logs (first boot takes a few minutes — it also runs `sql/init/*.sql` automatically).

### 3. Generate synthetic source data
```bash
python data/generators/generate_all.py
```

### 4. Run the pipeline manually (or trigger via Airflow UI at localhost:8080)
```bash
python src/ingestion/load_raw.py
```
Then run the SQL scripts under `sql/staging`, `sql/dimensions`, `sql/facts`, `sql/marts` in order (or trigger the `build_sales_warehouse` and `refresh_sales_marts` DAGs from the Airflow UI, login `admin`/`admin`).

### 5. Run tests
```bash
python -m pytest tests/unit -v          # no dependencies required
python -m pytest tests/integration -v   # requires Oracle running
```

## Airflow DAGs

| DAG | Purpose |
|---|---|
| `ingest_sales_sources` | Extracts 7 sources into Oracle RAW (incremental where `updated_at` is available), validates row counts, records an `ETL_RUN` audit entry |
| `build_sales_warehouse` | Staging cleanup → dimension loads (SCD Type 2) → fact table loads |
| `refresh_sales_marts` | Refreshes all 4 BI marts from the DWH facts/dimensions |

## Data quality

12 rules spanning customer, product, and sales domains (not-null, email format, non-negative amounts, referential integrity, uniqueness, non-future dates, no duplicate loads), evaluated against RAW (pre-clean signal) and DWH (post-clean invariants), with results persisted to `AUDIT.DATA_QUALITY_RESULT` for historical tracking. See [src/validation/data_quality_checks.py](src/validation/data_quality_checks.py).

## Performance optimization

`FACT_SALES` is range-partitioned by year on `date_key`, with 3 local composite indexes. Execution plan comparison showed a **77.7% cost reduction** (1092 → 244) after indexing. A materialized view (`MV_MONTHLY_SALES_SUMMARY`) pre-aggregates monthly store-level sales. Full methodology and real measured numbers: [docs/performance-results.md](docs/performance-results.md).

## Power BI dashboard

4 pages, connected directly to Oracle (`DWH_OWNER` + `MART_OWNER` schemas):
1. **Executive Overview** — KPI cards, revenue trend, revenue vs target
2. **Product Performance** — revenue by category, top/bottom 10 products, return rate
3. **Customer Analytics** — lifetime value, top customers, revenue by segment, new vs returning
4. **Store Performance** — revenue by store, regional performance, target achievement, store profitability

Screenshots: [powerbi/screenshots](powerbi/screenshots)

## Known limitations

- **Sales targets are uncalibrated**: `sales_targets.csv` is generated independently at random (not derived from actual sales volume), so `target_achievement_percentage` in the Store Performance mart is artificially low (~13-16%). In a real system, targets would be set relative to historical actuals.
- **Return rate can exceed 100% at low volumes**: `MONTHLY_PRODUCT_PERFORMANCE.return_rate` is computed per product/month; for low-volume product-month combinations, randomly generated returns can outnumber that month's units sold, producing rates above 100%. This is a synthetic-data artifact, not a calculation bug — averaging across months (as done in the dashboard) mitigates it.
- **Single sales channel**: all orders are attributed to the `WEB` channel, since the source generator does not produce a `channel` field. `DIM_SALES_CHANNEL` exists and is ready to use if channel data were added.
- **Discount impact** (Product Performance page) was scoped out, since discount data lives only in `FACT_SALES`/`ORDER_ITEMS_CLEAN`, not in any mart.
- **RAW accumulates test-run duplicates**: because ingestion was run manually many times during development (non-incremental sources like `order_items`, `returns`, `stores`, `sales_targets` are full-extract every run), RAW row counts are higher than a single clean run would produce. Staging deduplication absorbs this correctly.

## CI/CD

GitHub Actions runs the unit test suite (26 tests) on every push/PR to `main`. Integration tests require a live Oracle instance and are run locally before pushing.
