from datetime import datetime, timedelta

from airflow import DAG
from airflow.exceptions import AirflowException
from airflow.operators.python import PythonOperator

default_args = {
    "owner": "novaretail",
    "retries": 2,
    "retry_delay": timedelta(minutes=2),
}


def _extract(fn_name, **context):
    import sys
    sys.path.insert(0, "/opt/airflow/src")
    from ingestion import load_raw

    batch_id = context["run_id"]
    fn = getattr(load_raw, fn_name)
    return fn(batch_id)


def _validate_raw_data(**context):
    ti = context["ti"]
    task_ids = [
        "extract_customers_json",
        "extract_products_csv",
        "extract_orders_api",
        "extract_order_items_csv",
        "extract_returns_csv",
        "extract_stores_csv",
        "extract_sales_targets_csv",
    ]
    counts = ti.xcom_pull(task_ids=task_ids)
    total = sum(c or 0 for c in counts)
    print(f"Rows extracted this run: {dict(zip(task_ids, counts))}")

    if total == 0:
        print("No new rows in this run (expected on repeated incremental runs) - OK.")
    return total


def _update_ingestion_audit(**context):
    import sys
    sys.path.insert(0, "/opt/airflow/src")
    from ingestion.load_raw import record_etl_run

    ti = context["ti"]
    batch_id = context["run_id"]
    start_time = context["dag_run"].start_date
    total_rows = ti.xcom_pull(task_ids="validate_raw_data") or 0

    record_etl_run(
        batch_id=batch_id,
        start_time=start_time,
        end_time=datetime.utcnow(),
        status="SUCCESS",
        rows_extracted=total_rows,
    )


with DAG(
    dag_id="ingest_sales_sources",
    default_args=default_args,
    description="Extract source files, validate, load into Oracle RAW, record audit",
    schedule_interval="@daily",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    dagrun_timeout=timedelta(minutes=30),
    tags=["ingestion", "raw"],
) as dag:

    extract_customers_json = PythonOperator(
        task_id="extract_customers_json",
        python_callable=_extract,
        op_kwargs={"fn_name": "extract_customers"},
    )

    extract_products_csv = PythonOperator(
        task_id="extract_products_csv",
        python_callable=_extract,
        op_kwargs={"fn_name": "extract_products"},
    )

    extract_orders_api = PythonOperator(
        task_id="extract_orders_api",
        python_callable=_extract,
        op_kwargs={"fn_name": "extract_orders"},
    )

    extract_order_items_csv = PythonOperator(
        task_id="extract_order_items_csv",
        python_callable=_extract,
        op_kwargs={"fn_name": "extract_order_items"},
    )

    extract_returns_csv = PythonOperator(
        task_id="extract_returns_csv",
        python_callable=_extract,
        op_kwargs={"fn_name": "extract_returns"},
    )

    extract_stores_csv = PythonOperator(
        task_id="extract_stores_csv",
        python_callable=_extract,
        op_kwargs={"fn_name": "extract_stores"},
    )

    extract_sales_targets_csv = PythonOperator(
        task_id="extract_sales_targets_csv",
        python_callable=_extract,
        op_kwargs={"fn_name": "extract_sales_targets"},
    )

    validate_raw_data = PythonOperator(
        task_id="validate_raw_data",
        python_callable=_validate_raw_data,
    )

    update_ingestion_audit = PythonOperator(
        task_id="update_ingestion_audit",
        python_callable=_update_ingestion_audit,
    )

    extract_tasks = [
        extract_customers_json,
        extract_products_csv,
        extract_orders_api,
        extract_order_items_csv,
        extract_returns_csv,
        extract_stores_csv,
        extract_sales_targets_csv,
    ]

    extract_tasks >> validate_raw_data >> update_ingestion_audit