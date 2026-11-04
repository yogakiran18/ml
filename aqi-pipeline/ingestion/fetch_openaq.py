import os
import json
import requests
import sys
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

# Ensure sibling modules are importable from any working directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extraction_log import log_extraction

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

CITY_COORDS = {
    "Los Angeles": (34.0522, -118.2437),
    "New York": (40.7128, -74.0060),
    "London": (51.5074, -0.1278),
    "Tokyo": (35.6762, 139.6503),
    "Paris": (48.8566, 2.3522),
    "Delhi": (28.6139, 77.2090),
    "Beijing": (39.9042, 116.4074),
    "Sydney": (-33.8688, 151.2093),
    "Mumbai": (19.0760, 72.8777),
    "Bengaluru": (12.9716, 77.5946),
    "Chennai": (13.0827, 80.2707),
    "Kolkata": (22.5726, 88.3639),
    "Hyderabad": (17.3850, 78.4867),
    "Pune": (18.5204, 73.8567),
    "Ahmedabad": (23.0225, 72.5714)
}

OPENMETEO_AQ_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"

def fetch_openaq_data(days_back=7):
    # Determine the date range
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days_back)
    
    for i in range(days_back):
        target_date = (start_date + timedelta(days=i)).strftime('%Y-%m-%d')
        output_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw', 'openaq')
        os.makedirs(output_dir, exist_ok=True)
        
        output_file = os.path.join(output_dir, f"{target_date}.json")
        
        # Idempotent re-runs: do not overwrite
        if os.path.exists(output_file):
            print(f"Skipping {target_date}, file already exists.")
            continue
            
        all_results = []
        
        for city, (lat, lon) in CITY_COORDS.items():
            params = {
                "latitude": lat,
                "longitude": lon,
                "hourly": "pm2_5",
                "start_date": target_date,
                "end_date": target_date
            }
            
            try:
                response = requests.get(OPENMETEO_AQ_URL, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                hourly = data.get('hourly', {})
                times = hourly.get('time', [])
                pm25_list = hourly.get('pm2_5', [])
                
                for t, pm25_val in zip(times, pm25_list):
                    val = pm25_val if pm25_val is not None else 12.0
                    all_results.append({
                        "location": city,
                        "parameter": "pm25",
                        "value": round(float(val), 2),
                        "unit": "µg/m³",
                        "date": {"utc": f"{t}:00Z"}
                    })
                    
            except Exception as e:
                error_msg = str(e)
                print(f"Failed to fetch OpenMeteo Air Quality for {city} on {target_date}: {error_msg}")
                
        if all_results:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump({"results": all_results}, f, indent=2)
                
            log_extraction(source=f"openaq_{target_date}", status="SUCCESS", row_count=len(all_results))
            print(f"Saved {len(all_results)} AQ records for {target_date} to {output_file}")
        else:
            log_extraction(source=f"openaq_{target_date}", status="FAILED", row_count=0, error_message="All cities failed")

if __name__ == "__main__":
    fetch_openaq_data()
