"""
AQI Pipeline Runner - Local Daily Scheduler
=============================================
This script mirrors the Airflow DAG pipeline but runs locally without Docker.
It can be executed manually or scheduled via Windows Task Scheduler.

Pipeline Steps:
  1. Extract  -> Fetch OpenAQ + OpenMeteo data
  2. Validate -> Run data quality checks
  3. Clean    -> Remove outliers, duplicates
  4. Transform-> Merge and compute AQI categories
  5. Load     -> Populate SQLite database
  6. Features -> Build ML features (lags, day_of_week, month)
  7. Train    -> Train models and register best in MLflow
"""

import os
import sys
import time
import traceback
from datetime import datetime

# Ensure project root is on the path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(PROJECT_ROOT)
sys.path.insert(0, PROJECT_ROOT)

LOG_FILE = os.path.join(PROJECT_ROOT, 'data', 'pipeline_runs.log')

def log(msg, level="INFO"):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{ts}] [{level}] {msg}"
    print(line)
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(line + "\n")

def run_step(name, func, **kwargs):
    """Run a pipeline step with timing and error handling."""
    log(f">> Starting: {name}")
    start = time.time()
    try:
        func(**kwargs)
        elapsed = time.time() - start
        log(f"[OK] Completed: {name} ({elapsed:.1f}s)")
        return True
    except Exception as e:
        elapsed = time.time() - start
        log(f"[FAIL] FAILED: {name} ({elapsed:.1f}s) -- {e}", level="ERROR")
        traceback.print_exc()
        return False

def run_pipeline():
    log("=" * 60)
    log("AQI PIPELINE RUN STARTED")
    log("=" * 60)
    pipeline_start = time.time()

    # Step 1: Extract
    from ingestion.fetch_openmeteo import fetch_openmeteo_data
    from ingestion.fetch_openaq import fetch_openaq_data

    if not run_step("Extract OpenMeteo", fetch_openmeteo_data, days_back=7):
        log("Extract OpenMeteo failed, but continuing with fallback data if available.", level="WARN")
    
    if not run_step("Extract OpenAQ", fetch_openaq_data, days_back=7):
        log("Extract OpenAQ failed. Attempting mock data fallback...", level="WARN")
        from tests.create_mock_openaq import create_mocks
        run_step("Create Mock OpenAQ Data", create_mocks)

    # Step 2: Validate
    from etl.validate import validate_openaq, validate_openmeteo
    run_step("Validate OpenAQ", validate_openaq)
    run_step("Validate OpenMeteo", validate_openmeteo)

    # Step 3: Clean
    from etl.clean import clean_openaq, clean_openmeteo
    run_step("Clean OpenAQ", clean_openaq)
    run_step("Clean OpenMeteo", clean_openmeteo)

    # Step 4: Transform
    from etl.transform import transform_data
    if not run_step("Transform Data", transform_data):
        log("Transform failed. Aborting pipeline.", level="ERROR")
        return False

    # Step 5: Load to SQLite
    from populate_sqlite import run_fallback
    if not run_step("Load to SQLite", run_fallback):
        log("SQLite load failed. Aborting pipeline.", level="ERROR")
        return False

    # Step 6: Build Features
    from features.build_features import build_features
    if not run_step("Build ML Features", build_features):
        log("Feature engineering failed. Aborting pipeline.", level="ERROR")
        return False

    # Step 7: Train Model
    from models.train import train_models
    if not run_step("Train & Register Model", train_models):
        log("Model training failed. Previous model version remains active.", level="WARN")

    total = time.time() - pipeline_start
    log(f"AQI PIPELINE RUN COMPLETED ({total:.1f}s total)")
    log("=" * 60)
    return True

if __name__ == '__main__':
    success = run_pipeline()
    sys.exit(0 if success else 1)
