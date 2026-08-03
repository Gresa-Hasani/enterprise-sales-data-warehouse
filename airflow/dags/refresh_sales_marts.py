from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

default_args = {
    "owner": "novaretail",
    "retries": 2,
    "retry_delay": timedelta(minutes=2),
}

SQL_BASE = "/opt/airflow/sql"


def _run(filepath, user, password_env, default_password):
    import sys, os
    sys.path.insert(0, "/opt/airflow/src")
    from utils.sql_runner import run_sql_file
    run_sql_file(filepath, user, os.getenv(password_env, default_password))


with DAG(
    dag_id="refresh_sales_marts",
    default_args=default_args,
    description="Refresh BI data marts from the DWH facts and dimensions",
    schedule_interval="@daily",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    dagrun_timeout=timedelta(minutes=30),
    tags=["marts", "bi"],
) as dag:

    refresh_daily_sales = PythonOperator(
        task_id="refresh_daily_sales",
        python_callable=_run,
        op_kwargs={
            "filepath": f"{SQL_BASE}/marts/02_load_mart_daily_sales.sql",
            "user": "mart_owner",
            "password_env": "ORACLE_MART_PASSWORD",
            "default_password": "MartPass2026",
        },
    )

    refresh_product_performance = PythonOperator(
        task_id="refresh_product_performance",
        python_callable=_run,
        op_kwargs={
            "filepath": f"{SQL_BASE}/marts/04_load_mart_monthly_product_performance.sql",
            "user": "mart_owner",
            "password_env": "ORACLE_MART_PASSWORD",
            "default_password": "MartPass2026",
        },
    )

    refresh_customer_summary = PythonOperator(
        task_id="refresh_customer_summary",
        python_callable=_run,
        op_kwargs={
            "filepath": f"{SQL_BASE}/marts/06_load_mart_customer_360_summary.sql",
            "user": "mart_owner",
            "password_env": "ORACLE_MART_PASSWORD",
            "default_password": "MartPass2026",
        },
    )

    refresh_store_performance = PythonOperator(
        task_id="refresh_store_performance",
        python_callable=_run,
        op_kwargs={
            "filepath": f"{SQL_BASE}/marts/08_load_mart_store_target_performance.sql",
            "user": "mart_owner",
            "password_env": "ORACLE_MART_PASSWORD",
            "default_password": "MartPass2026",
        },
    )

    # all 4 marts read independently from DWH facts/dims - no interdependency
    [
        refresh_daily_sales,
        refresh_product_performance,
        refresh_customer_summary,
        refresh_store_performance,
    ]