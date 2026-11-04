import os
import glob
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

STAGING_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'staging')
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

def get_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        database=os.getenv("POSTGRES_DB", "aqi_db"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres")
    )

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
    with open(schema_path, 'r') as f:
        cursor.execute(f.read())
    conn.commit()
    cursor.close()
    conn.close()

def load_staging_tables():
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Load Staging OpenAQ (Append-only, or truncate-load for staging)
    openaq_files = glob.glob(f"{STAGING_DIR}/openaq_valid_*.csv")
    if openaq_files:
        df = pd.concat([pd.read_csv(f) for f in openaq_files], ignore_index=True)
        cursor.execute("TRUNCATE TABLE stg_openaq;")
        df_subset = df[['location', 'parameter', 'value', 'unit', 'date_utc']].copy()
        df_subset['date_utc'] = pd.to_datetime(df_subset['date_utc'])
        records = df_subset.to_records(index=False).tolist()
        execute_values(cursor, "INSERT INTO stg_openaq (location, parameter, value, unit, date_utc) VALUES %s", records)
        print(f"Loaded {len(records)} rows into stg_openaq.")

    # 2. Load Staging OpenMeteo
    meteo_files = glob.glob(f"{STAGING_DIR}/openmeteo_valid_*.csv")
    if meteo_files:
        df = pd.concat([pd.read_csv(f) for f in meteo_files], ignore_index=True)
        cursor.execute("TRUNCATE TABLE stg_openmeteo;")
        df_subset = df[['time', 'temperature_2m', 'relative_humidity_2m', 'rain', 'wind_speed_10m']].copy()
        df_subset['time'] = pd.to_datetime(df_subset['time'])
        records = df_subset.to_records(index=False).tolist()
        execute_values(cursor, "INSERT INTO stg_openmeteo (time, temperature_2m, relative_humidity_2m, rain, wind_speed_10m) VALUES %s", records)
        print(f"Loaded {len(records)} rows into stg_openmeteo.")
        
    conn.commit()
    cursor.close()
    conn.close()

def load_clean_tables():
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Clean OpenAQ Upsert
    aq_clean = os.path.join(STAGING_DIR, 'openaq_clean.csv')
    if os.path.exists(aq_clean):
        df = pd.read_csv(aq_clean)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        records = df[['station', 'timestamp', 'parameter', 'value', 'unit']].to_records(index=False).tolist()
        upsert_query = """
            INSERT INTO cln_openaq (station, timestamp, parameter, value, unit)
            VALUES %s
            ON CONFLICT (station, timestamp, parameter) DO UPDATE SET
                value = EXCLUDED.value, unit = EXCLUDED.unit;
        """
        execute_values(cursor, upsert_query, records)
        print(f"Upserted {len(records)} rows into cln_openaq.")
        
    # 2. Clean OpenMeteo Upsert
    met_clean = os.path.join(STAGING_DIR, 'openmeteo_clean.csv')
    if os.path.exists(met_clean):
        df = pd.read_csv(met_clean)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        records = df[['station', 'timestamp', 'temperature_2m', 'relative_humidity_2m', 'rain', 'wind_speed_10m']].to_records(index=False).tolist()
        upsert_query = """
            INSERT INTO cln_openmeteo (station, timestamp, temperature_2m, relative_humidity_2m, rain, wind_speed_10m)
            VALUES %s
            ON CONFLICT (station, timestamp) DO UPDATE SET
                temperature_2m = EXCLUDED.temperature_2m,
                relative_humidity_2m = EXCLUDED.relative_humidity_2m,
                rain = EXCLUDED.rain,
                wind_speed_10m = EXCLUDED.wind_speed_10m;
        """
        execute_values(cursor, upsert_query, records)
        print(f"Upserted {len(records)} rows into cln_openmeteo.")
        
    conn.commit()
    cursor.close()
    conn.close()

def load_gold_table():
    conn = get_connection()
    cursor = conn.cursor()
    
    trans_csv = os.path.join(STAGING_DIR, 'transformed_data.csv')
    if os.path.exists(trans_csv):
        df = pd.read_csv(trans_csv)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['date'] = df['timestamp'].dt.date
        
        daily_df = df.groupby(['station', 'date']).agg({
            'pm25_avg': 'mean',
            'temperature_2m': 'mean'
        }).reset_index()
        
        def get_aqi(pm25):
            if pd.isna(pm25): return "Unknown"
            elif pm25 <= 12.0: return "Good"
            elif pm25 <= 35.4: return "Moderate"
            elif pm25 <= 55.4: return "Unhealthy for Sensitive Groups"
            elif pm25 <= 150.4: return "Unhealthy"
            elif pm25 <= 250.4: return "Very Unhealthy"
            else: return "Hazardous"
            
        daily_df['aqi_category'] = daily_df['pm25_avg'].apply(get_aqi)
        records = daily_df[['station', 'date', 'pm25_avg', 'temperature_2m', 'aqi_category']].to_records(index=False).tolist()
        
        upsert_query = """
            INSERT INTO gold_daily_aqi_by_station (station, date, pm25_avg, temperature_2m_avg, aqi_category)
            VALUES %s
            ON CONFLICT (station, date) DO UPDATE SET
                pm25_avg = EXCLUDED.pm25_avg,
                temperature_2m_avg = EXCLUDED.temperature_2m_avg,
                aqi_category = EXCLUDED.aqi_category;
        """
        execute_values(cursor, upsert_query, records)
        print(f"Upserted {len(records)} rows into gold_daily_aqi_by_station.")
        
    conn.commit()
    cursor.close()
    conn.close()

def count_rows():
    conn = get_connection()
    cursor = conn.cursor()
    tables = ['stg_openaq', 'stg_openmeteo', 'cln_openaq', 'cln_openmeteo', 'gold_daily_aqi_by_station']
    print("\n--- POSTGRES ROW COUNTS ---")
    for t in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {t}")
        count = cursor.fetchone()[0]
        print(f"{t}: {count} rows")
    cursor.close()
    conn.close()

if __name__ == "__main__":
    try:
        init_db()
        load_staging_tables()
        load_clean_tables()
        load_gold_table()
        count_rows()
    except Exception as e:
        print(f"Error loading to database: {e}")
