import sqlite3
import pandas as pd
import mlflow
import mlflow.sklearn
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error
from mlflow.models import infer_signature
import numpy as np
import os

# Ensure tracking URI is set correctly for local sqlite
os.makedirs('mlflow', exist_ok=True)
mlflow.set_tracking_uri("sqlite:///mlflow/mlflow.db")
mlflow.set_experiment("AQI_Prediction")

def load_data():
    conn = sqlite3.connect('aqi_db.sqlite')
    df = pd.read_sql("SELECT * FROM ml_features ORDER BY date", conn)
    conn.close()
    return df

def train_models():
    df = load_data()
    
    if len(df) < 2:
        print("Not enough data to train models.")
        return

    # One-hot encode stations so the model learns city-specific baselines
    df = pd.get_dummies(df, columns=['station'], dtype=int)
    
    # Chronological split
    # Since we only have a few rows locally, we'll split at 80% chronologically
    split_idx = int(len(df) * 0.8)
    if split_idx == 0:
        split_idx = 1
    if split_idx == len(df):
        split_idx = len(df) - 1
        
    train_df = df.iloc[:split_idx]
    test_df = df.iloc[split_idx:]
    
    features = ['lag_1_pm25', 'lag_1_temp', 'temperature_2m_avg', 'day_of_week', 'month']
    dummy_cols = [col for col in df.columns if col.startswith('station_')]
    features.extend(dummy_cols)
    
    target = 'pm25_avg'
    
    X_train = train_df[features]
    y_train = train_df[target]
    
    X_test = test_df[features]
    y_test = test_df[target]

    models = [
        ("Linear Regression", LinearRegression(), {}),
        ("Random Forest", RandomForestRegressor(n_estimators=10, random_state=42), {"n_estimators": 10})
    ]

    best_rmse = float('inf')
    best_run_id = None
    best_model_name = None

    print(f"Training on {len(X_train)} samples, testing on {len(X_test)} samples.")

    for model_name, model, params in models:
        with mlflow.start_run(run_name=model_name) as run:
            model.fit(X_train, y_train)
            preds = model.predict(X_test)
            
            rmse = np.sqrt(mean_squared_error(y_test, preds))
            mae = mean_absolute_error(y_test, preds)
            
            mlflow.log_params(params)
            mlflow.log_metric("rmse", rmse)
            mlflow.log_metric("mae", mae)
            
            signature = infer_signature(X_train, preds)
            mlflow.sklearn.log_model(model, "model", signature=signature)
            
            print(f"Model: {model_name} | RMSE: {rmse:.2f} | MAE: {mae:.2f}")
            
            if rmse < best_rmse:
                best_rmse = rmse
                best_run_id = run.info.run_id
                best_model_name = model_name

    if best_run_id:
        print(f"Registering {best_model_name} as best model (run_id: {best_run_id})...")
        model_uri = f"runs:/{best_run_id}/model"
        result = mlflow.register_model(model_uri, "AQI_Predictor_Global")
        print(f"Registered Model: AQI_Predictor_Global, Version: {result.version}")

if __name__ == '__main__':
    train_models()
