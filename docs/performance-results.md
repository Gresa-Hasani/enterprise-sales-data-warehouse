# Performance Optimization Results                
                                   
## Context                                        
Table: `DWH_OWNER.FACT_SALES` (13,009 rows, partitioned by `date_key` into 6 range partitions: P_2023â€“P_2027, P_FUTURE)                             
                           
## Test query                                     
```sql              
SELECT COUNT(*), SUM(net_amount) FROM FACT_SALES WHERE store_key = 5;
```

## Partitioning
- Converted FACT_SALES from a non-partitioned heap table to RANGE partitioning on `date_key` (format YYYYMMDD).
- Verified row distribution across partitions after DBMS_STATS.GATHER_TABLE_STATS:
  - P_2023: 6,968 rows
  - P_2024: 2,193 rows
  - P_2025: 2,360 rows
  - P_2026: 1,488 rows
  - P_2027: 0 rows
  - P_FUTURE: 0 rows
  - Total: 13,009 (matches pre-partitioning count)

## Indexes added
```sql
CREATE INDEX idx_fact_sales_customer_date ON FACT_SALES (customer_key, date_key) LOCAL;
CREATE INDEX idx_fact_sales_product_date ON FACT_SALES (product_key, date_key) LOCAL;
CREATE INDEX idx_fact_sales_store_date ON FACT_SALES (store_key, date_key) LOCAL;
```

## Execution plan comparison (measured, not estimated)

**Before (forced full scan via hint):**
```
TABLE ACCESS FULL | FACT_SALES | Cost = 1092
```

**After (optimizer naturally chose the index):**
```
TABLE ACCESS BY LOCAL INDEX ROWID BATCHED | FACT_SALES
  INDEX RANGE SCAN | IDX_FACT_SALES_STORE_DATE | Cost = 244
```

**Cost reduction: 1092 â†’ 244 (77.7% improvement)**

## Note on elapsed time
At this data volume (13,009 rows total, 617 matching rows for store_key=5),
wall-clock `Elapsed` time showed no meaningful difference (0.00s vs 0.01s) â€”
both plans execute fast enough that Oracle XE overhead dominates over the
actual scan cost. The optimizer's cost estimate (1092 vs 244) is the
reliable signal here, and confirms the index is being used correctly and
would matter at production scale (millions of rows, per the original
project sizing of 3-5M order items).

## Materialized View
Created `DWH_OWNER.MV_MONTHLY_SALES_SUMMARY` to pre-aggregate monthly
revenue/profit/units per store, avoiding repeated GROUP BY scans over
FACT_SALES for reporting queries at this grain.

```sql
CREATE MATERIALIZED VIEW dwh_owner.MV_MONTHLY_SALES_SUMMARY
BUILD IMMEDIATE
REFRESH COMPLETE ON DEMAND
AS
SELECT
    d.year_number, d.month_number, s.store_id, s.store_name,
    SUM(f.net_amount) AS revenue,
    SUM(f.profit_amount) AS profit,
    SUM(f.quantity) AS units_sold,
    COUNT(DISTINCT f.order_id) AS order_count
FROM dwh_owner.FACT_SALES f
JOIN dwh_owner.DIM_DATE d ON d.date_key = f.date_key
JOIN dwh_owner.DIM_STORE s ON s.store_key = f.store_key
GROUP BY d.year_number, d.month_number, s.store_id, s.store_name;
```

Verified:
- Row count: 1,310 (store x year x month combinations)
- `EXEC DBMS_MVIEW.REFRESH('MV_MONTHLY_SALES_SUMMARY', 'C')` completes successfully
  (complete refresh, on demand â€” matches `REFRESH COMPLETE ON DEMAND` clause)

Required system privilege `CREATE MATERIALIZED VIEW` was not included in the
`RESOURCE` role granted at schema setup time; had to be granted explicitly to
`dwh_owner` to allow this object type.