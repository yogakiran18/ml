import sqlite3
import pandas as pd
import mlflow
import mlflow.sklearn
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import numpy as np
import matplotlib.pyplot as plt
import os

def load_test_data():
    conn = sqlite3.connect('aqi_db.sqlite')
    df = pd.read_sql("SELECT * FROM ml_features ORDER BY date", conn)
    conn.close()
    
    if len(df) < 2:
        raise ValueError("Not enough data to evaluate.")
        
    split_idx = int(len(df) * 0.8)
    if split_idx == 0: split_idx = 1
    if split_idx == len(df): split_idx = len(df) - 1
    
    test_df = df.iloc[split_idx:]
    return test_df

def evaluate_model():
    mlflow.set_tracking_uri("sqlite:///mlflow/mlflow.db")
    
    # Load model
    model_name = "AQI_Predictor_LA"
    model_version = "1"
    
    print(f"Loading {model_name} version {model_version}...")
    model_uri = f"models:/{model_name}/{model_version}"
    model = mlflow.sklearn.load_model(model_uri)
    
    test_df = load_test_data()
    features = ['lag_1_pm25', 'lag_1_temp', 'temperature_2m_avg', 'day_of_week', 'month']
    target = 'pm25_avg'
    
    X_test = test_df[features]
    y_test = test_df[target]
    
    # Predict
    preds = model.predict(X_test)
    
    # Metrics
    rmse = np.sqrt(mean_squared_error(y_test, preds))
    mae = mean_absolute_error(y_test, preds)
    # Handle R2 warning if only one or two samples
    r2 = r2_score(y_test, preds) if len(y_test) > 1 else float('nan')
    
    print("\n--- Model Evaluation Report ---")
    print(f"RMSE: {rmse:.2f}")
    print(f"MAE:  {mae:.2f}")
    print(f"R²:   {r2:.2f}")
    
    # Plotting
    plt.figure(figsize=(10, 5))
    plt.plot(pd.to_datetime(test_df['date']), y_test, label='Actual PM2.5', marker='o')
    plt.plot(pd.to_datetime(test_df['date']), preds, label='Predicted PM2.5', marker='x', linestyle='--')
    plt.title('AQI PM2.5 Prediction vs Actual (Test Set)')
    plt.xlabel('Date')
    plt.ylabel('PM2.5 Avg')
    plt.legend()
    plt.grid(True)
    
    os.makedirs('docs', exist_ok=True)
    plot_path = 'docs/evaluate_plot.png'
    plt.savefig(plot_path)
    print(f"\nPlot saved to {plot_path}")
    
    # Written Summary Analysis
    residuals = np.abs(y_test - preds)
    worst_idx = residuals.idxmax()
    worst_date = test_df.loc[worst_idx, 'date']
    worst_actual = test_df.loc[worst_idx, 'pm25_avg']
    worst_pred = preds[np.where(test_df.index == worst_idx)[0][0]]
    
    print("\n--- Error Analysis Summary ---")
    print(f"The model performed worst on {worst_date}, missing the actual value ({worst_actual:.2f}) "
          f"by {residuals[worst_idx]:.2f} (Predicted: {worst_pred:.2f}).")
    print("Potential reasons for poor performance on this date:")
    print("1. Sudden meteorological shifts (e.g., unexpected temperature drops) not fully captured by simple lags.")
    print("2. External pollutant spikes (e.g., local events, fires) that lack direct features in the current dataset.")
    print("3. Small training size in this local mock environment.")

if __name__ == '__main__':
    evaluate_model()
