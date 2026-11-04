import sqlite3
import datetime

def init_db():
    conn = sqlite3.connect('aqi_db.sqlite')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prediction_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME,
            model_version TEXT,
            lag_1_pm25 REAL,
            lag_1_temp REAL,
            temperature_2m_avg REAL,
            day_of_week INTEGER,
            month INTEGER,
            predicted_pm25 REAL,
            actual_pm25 REAL,
            error REAL
        )
    ''')
    conn.commit()
    conn.close()

def log_prediction(features: dict, predicted_pm25: float, model_version: str):
    """
    Logs each prediction served so actual vs predicted can be computed retrospectively.
    """
    conn = sqlite3.connect('aqi_db.sqlite')
    cursor = conn.cursor()
    
    timestamp = datetime.datetime.utcnow().isoformat()
    
    cursor.execute('''
        INSERT INTO prediction_logs 
        (timestamp, model_version, lag_1_pm25, lag_1_temp, temperature_2m_avg, day_of_week, month, predicted_pm25)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        timestamp,
        model_version,
        features.get('lag_1_pm25'),
        features.get('lag_1_temp'),
        features.get('temperature_2m_avg'),
        features.get('day_of_week'),
        features.get('month'),
        predicted_pm25
    ))
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    # Initialize the table when run as a script
    init_db()
    print("Prediction log table initialized.")
