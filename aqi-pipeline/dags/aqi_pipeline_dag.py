from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

import sys
import os
# Ensure the parent directory is in the PYTHONPATH so we can import modules
sys.path.insert(0, '/opt/airflow')

from ingestion.fetch_openaq import fetch_openaq_data
from ingestion.fetch_openmeteo import fetch_openmeteo_data
from etl.validate import validate_openaq, validate_openmeteo
from etl.clean import clean_openaq, clean_openmeteo
from etl.transform import transform_data
from populate_sqlite import run_fallback
from features.build_features import build_features
from models.train import train_models

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'aqi_pipeline',
    default_args=default_args,
    description='AQI Data Engineering Pipeline',
    schedule_interval=timedelta(days=1),
    start_date=datetime(2026, 9, 1),
    catchup=False,
    tags=['aqi'],
) as dag:

    extract_aq_task = PythonOperator(
        task_id='extract_openaq',
        python_callable=fetch_openaq_data,
        op_kwargs={'days_back': 7},
    )

    extract_meteo_task = PythonOperator(
        task_id='extract_openmeteo',
        python_callable=fetch_openmeteo_data,
        op_kwargs={'days_back': 7},
    )

    def run_validations():
        validate_openaq()
        validate_openmeteo()

    validate_task = PythonOperator(
        task_id='validate',
        python_callable=run_validations,
    )

    def run_cleaning():
        clean_openaq()
        clean_openmeteo()

    clean_task = PythonOperator(
        task_id='clean',
        python_callable=run_cleaning,
    )

    transform_task = PythonOperator(
        task_id='transform',
        python_callable=transform_data,
    )

    load_task = PythonOperator(
        task_id='load_to_sqlite',
        python_callable=run_fallback,
    )

    build_features_task = PythonOperator(
        task_id='build_features',
        python_callable=build_features,
    )

    train_model_task = PythonOperator(
        task_id='train_model',
        python_callable=train_models,
    )

    # Chain dependencies
    extract_aq_task >> extract_meteo_task >> validate_task >> clean_task >> transform_task >> load_task >> build_features_task >> train_model_task
