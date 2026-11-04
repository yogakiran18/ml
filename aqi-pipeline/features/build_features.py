import sqlite3
import pandas as pd
import os

def build_features():
    db_path = 'aqi_db.sqlite'
    if not os.path.exists(db_path):
        print(f"Database {db_path} not found.")
        return

    conn = sqlite3.connect(db_path)
    
    # Read gold data
    # Read gold data
    query = "SELECT * FROM gold_daily_aqi_by_station ORDER BY date"
    df = pd.read_sql(query, conn)
    
    if df.empty:
        print("No data found in gold_daily_aqi_by_station.")
        conn.close()
        return

    # Create basic features
    df['date'] = pd.to_datetime(df['date'])
    
    # Target variable: pm25_avg
    # Features:
    # 1. Previous day's PM2.5 (lag_1)
    # 2. Previous day's temperature (temp_lag_1)
    # 3. Current day's temperature (temperature_2m_avg)
    # 4. Day of week
    # 5. Month
    
    df['lag_1_pm25'] = df.groupby('station')['pm25_avg'].shift(1)
    df['lag_1_temp'] = df.groupby('station')['temperature_2m_avg'].shift(1)
    df['day_of_week'] = df['date'].dt.dayofweek
    df['month'] = df['date'].dt.month
    
    # Drop first row of EACH station because it will have NaNs from shifting
    df = df.dropna()
    
    # Save to ml_features table
    df.to_sql('ml_features', conn, if_exists='replace', index=False)
    print(f"Successfully wrote {len(df)} rows to ml_features table.")
    
    conn.close()

if __name__ == '__main__':
    build_features()
