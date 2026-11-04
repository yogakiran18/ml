import os
import glob
import pandas as pd

STAGING_DIR = "data/staging"

def to_naive_utc(series):
    dt = pd.to_datetime(series, format='mixed')
    if dt.dt.tz is not None:
        return dt.dt.tz_convert(None)
    return dt

def clean_openaq():
    files = glob.glob(f"{STAGING_DIR}/openaq_valid_*.csv")
    if not files:
        return
        
    df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
    
    # Normalize timestamps to UTC (naive)
    df['timestamp'] = to_naive_utc(df['date_utc'])
    
    # Standardize station names
    df['station'] = df['location'].str.strip().str.title()
    
    # Standardize units
    if 'unit' in df.columns:
        df['unit'] = df['unit'].str.replace('ug/m3', 'µg/m³')
    
    df.to_csv(f"{STAGING_DIR}/openaq_clean.csv", index=False)

def clean_openmeteo():
    files = glob.glob(f"{STAGING_DIR}/openmeteo_valid_*.csv")
    if not files:
        return
        
    df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
    
    # Normalize timestamps to UTC (naive)
    df['timestamp'] = to_naive_utc(df['time'])
    
    # Station name is now propagated from the validation step, so we don't hardcode it.
    
    df.to_csv(f"{STAGING_DIR}/openmeteo_clean.csv", index=False)

if __name__ == "__main__":
    print("--- CLEANING ---")
    clean_openaq()
    clean_openmeteo()
    print("Clean step completed successfully.")
