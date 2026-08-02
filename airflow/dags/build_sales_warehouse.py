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
    dag_id="build_sales_warehouse",
    default_args=default_args,
    description="Build staging, dimensions and fact tables in Oracle DWH",
    schedule_interval="@daily",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    dagrun_timeout=timedelta(hours=1),
    tags=["staging", "dwh", "facts"],
) as dag:

    prepare_staging = PythonOperator(
        task_id="prepare_staging",
        python_callable=_run,
        op_kwargs={
            "filepath": f"{SQL_BASE}/staging/02_load_stg_customers_clean.sql",
            "user": "stg_owner",
            "password_env": "ORACLE_STG_PASSWORD",
            "default_password": "StgPass2026",
        },
    )

    load_products_clean = PythonOperator(
        task_id="load_products_clean",
        python_callable=_run,
        op_kwargs={
            "filepath": f"{SQL_BASE}/staging/04_load_stg_products_clean.sql",
            "user": "stg_owner",
            "password_env": "ORACLE_STG_PASSWORD",
            "default_password": "StgPass2026",
        },
    )

    load_orders_clean = PythonOperator(
        task_id="load_orders_clean",
        python_callable=_run,
        op_kwargs={
            "filepath": f"{SQL_BASE}/staging/06_load_stg_orders_clean.sql",
            "user": "stg_owner",
            "password_env": "ORACLE_STG_PASSWORD",
            "default_password": "StgPass2026",
        },
    )

    load_order_items_clean = PythonOperator(
        task_id="load_order_items_clean",
        python_callable=_run,
        op_kwargs={
            "filepath": f"{SQL_BASE}/staging/08_load_stg_order_items_clean.sql",
            "user": "stg_owner",
            "password_env": "ORACLE_STG_PASSWORD",
            "default_password": "StgPass2026",
        },
    )

    load_returns_clean = PythonOperator(
        task_id="load_returns_clean",
        python_callable=_run,
        op_kwargs={
            "filepath": f"{SQL_BASE}/staging/10_load_stg_returns_clean.sql",
            "user": "stg_owner",
            "password_env": "ORACLE_STG_PASSWORD",
            "default_password": "StgPass2026",
        },
    )

    load_dim_store = PythonOperator(
        task_id="load_dim_store",
        python_callable=_run,
        op_kwargs={
            "filepath": f"{SQL_BASE}/dimensions/04_load_dim_store.sql",
            "user": "dwh_owner",
            "password_env": "ORACLE_DWH_PASSWORD",
            "default_password": "DwhPass2026",
        },
    )

    load_dim_customer = PythonOperator(
        task_id="load_dim_customer",
        python_callable=_run,
        op_kwargs={
            "filepath": f"{SQL_BASE}/dimensions/08_load_dim_customer_scd2.sql",
            "user": "dwh_owner",
            "password_env": "ORACLE_DWH_PASSWORD",
            "default_password": "DwhPass2026",
        },
    )

    load_dim_product = PythonOperator(
        task_id="load_dim_product",
        python_callable=_run,
        op_kwargs={
            "filepath": f"{SQL_BASE}/dimensions/10_load_dim_product_scd2.sql",
            "user": "dwh_owner",
            "password_env": "ORACLE_DWH_PASSWORD",
            "default_password": "DwhPass2026",
        },
    )

    load_fact_sales = PythonOperator(
        task_id="load_fact_sales",
        python_callable=_run,
        op_kwargs={
            "filepath": f"{SQL_BASE}/facts/02_load_fact_sales.sql",
            "user": "dwh_owner",
            "password_env": "ORACLE_DWH_PASSWORD",
            "default_password": "DwhPass2026",
        },
    )

    load_fact_returns = PythonOperator(
        task_id="load_fact_returns",
        python_callable=_run,
        op_kwargs={
            "filepath": f"{SQL_BASE}/facts/04_load_fact_returns.sql",
            "user": "dwh_owner",
            "password_env": "ORACLE_DWH_PASSWORD",
            "default_password": "DwhPass2026",
        },
    )

    load_fact_sales_target = PythonOperator(
        task_id="load_fact_sales_target",
        python_callable=_run,
        op_kwargs={
            "filepath": f"{SQL_BASE}/facts/06_load_fact_sales_target.sql",
            "user": "dwh_owner",
            "password_env": "ORACLE_DWH_PASSWORD",
            "default_password": "DwhPass2026",
        },
    )

    prepare_staging >> load_products_clean >> load_orders_clean >> load_order_items_clean >> load_returns_clean

    load_returns_clean >> [load_dim_store, load_dim_customer, load_dim_product]

    [load_dim_store, load_dim_customer, load_dim_product] >> load_fact_sales
    load_fact_sales >> load_fact_returns
    load_dim_store >> load_fact_sales_target