import sqlite3
import pandas as pd
import os

STAGING_DIR = os.path.join('data', 'staging')

def get_aqi(pm25):
    if pd.isna(pm25): return "Unknown"
    elif pm25 <= 12.0: return "Good"
    elif pm25 <= 35.4: return "Moderate"
    elif pm25 <= 55.4: return "Unhealthy for Sensitive Groups"
    elif pm25 <= 150.4: return "Unhealthy"
    elif pm25 <= 250.4: return "Very Unhealthy"
    else: return "Hazardous"

def run_fallback():
    conn = sqlite3.connect('aqi_db.sqlite')

    # 1. Gold Daily
    df = pd.read_csv(os.path.join(STAGING_DIR, 'transformed_data.csv'))
    df['date'] = pd.to_datetime(df['timestamp']).dt.date
    daily_df = df.groupby(['station', 'date']).agg({'pm25_avg': 'mean', 'temperature_2m': 'mean'}).reset_index()
    daily_df.rename(columns={'temperature_2m': 'temperature_2m_avg'}, inplace=True)
    daily_df['aqi_category'] = daily_df['pm25_avg'].apply(get_aqi)
    daily_df.to_sql('gold_daily_aqi_by_station', conn, if_exists='replace', index=False)

    # 2. Clean OpenAQ
    aq = pd.read_csv(os.path.join(STAGING_DIR, 'openaq_clean.csv'))
    aq.to_sql('cln_openaq', conn, if_exists='replace', index=False)

    # 3. Clean OpenMeteo
    met = pd.read_csv(os.path.join(STAGING_DIR, 'openmeteo_clean.csv'))
    met.to_sql('cln_openmeteo', conn, if_exists='replace', index=False)

    conn.close()
    print("Populated SQLite fallback database successfully.")

if __name__ == '__main__':
    run_fallback()
