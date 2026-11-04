import pandas as pd
import os

STAGING_DIR = "data/staging"

def calculate_aqi_us_epa(pm25):
    """
    US EPA PM2.5 AQI Breakpoints (Standard used for this calculation):
    0.0 - 12.0: Good (0-50)
    12.1 - 35.4: Moderate (51-100)
    35.5 - 55.4: Unhealthy for Sensitive Groups (101-150)
    55.5 - 150.4: Unhealthy (151-200)
    150.5 - 250.4: Very Unhealthy (201-300)
    250.5+: Hazardous (301+)
    """
    if pd.isna(pm25):
        return "Unknown"
    elif pm25 <= 12.0:
        return "Good"
    elif pm25 <= 35.4:
        return "Moderate"
    elif pm25 <= 55.4:
        return "Unhealthy for Sensitive Groups"
    elif pm25 <= 150.4:
        return "Unhealthy"
    elif pm25 <= 250.4:
        return "Very Unhealthy"
    else:
        return "Hazardous"

def transform_data():
    if not os.path.exists(f"{STAGING_DIR}/openaq_clean.csv") or not os.path.exists(f"{STAGING_DIR}/openmeteo_clean.csv"):
        print("Clean data not found.")
        return
        
    aq_df = pd.read_csv(f"{STAGING_DIR}/openaq_clean.csv")
    meteo_df = pd.read_csv(f"{STAGING_DIR}/openmeteo_clean.csv")
    
    aq_df['timestamp'] = pd.to_datetime(aq_df['timestamp'])
    meteo_df['timestamp'] = pd.to_datetime(meteo_df['timestamp'])
    
    aq_pm25 = aq_df[aq_df['parameter'] == 'pm25'].copy()
    hourly_aq = aq_pm25.groupby(['station', 'timestamp'])['value'].mean().reset_index()
    hourly_aq.rename(columns={'value': 'pm25_avg'}, inplace=True)
    
    merged = pd.merge(hourly_aq, meteo_df, on=['station', 'timestamp'], how='inner')
    merged['aqi_category'] = merged['pm25_avg'].apply(calculate_aqi_us_epa)
    merged.to_csv(f"{STAGING_DIR}/transformed_data.csv", index=False)
    
    print("--- TRANSFORMATION ---")
    print(f"Transformed data: {len(merged)} hourly rows.")
    print("\n--- SAMPLE TRANSFORMED DATA ---")
    print(merged[['station', 'timestamp', 'pm25_avg', 'aqi_category', 'temperature_2m']].head(10).to_string(index=False))

if __name__ == "__main__":
    transform_data()
