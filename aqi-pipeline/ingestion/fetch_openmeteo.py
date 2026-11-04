import os
import json
import requests
import sys
from datetime import datetime, timedelta, timezone

# Ensure sibling modules are importable from any working directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extraction_log import log_extraction

# Global Cities
CITIES = {
    "Los Angeles": {"lat": 34.0522, "lon": -118.2437},
    "New York": {"lat": 40.7128, "lon": -74.0060},
    "London": {"lat": 51.5074, "lon": -0.1278},
    "Tokyo": {"lat": 35.6762, "lon": 139.6503},
    "Paris": {"lat": 48.8566, "lon": 2.3522},
    "Delhi": {"lat": 28.6139, "lon": 77.2090},
    "Beijing": {"lat": 39.9042, "lon": 116.4074},
    "Sydney": {"lat": -33.8688, "lon": 151.2093},
    "Mumbai": {"lat": 19.0760, "lon": 72.8777},
    "Bengaluru": {"lat": 12.9716, "lon": 77.5946},
    "Chennai": {"lat": 13.0827, "lon": 80.2707},
    "Kolkata": {"lat": 22.5726, "lon": 88.3639},
    "Hyderabad": {"lat": 17.3850, "lon": 78.4867},
    "Pune": {"lat": 18.5204, "lon": 73.8567},
    "Ahmedabad": {"lat": 23.0225, "lon": 72.5714}
}

def fetch_openmeteo_data(days_back=7):
    # For recent historical data, we can use the forecast endpoint with past_days
    forecast_url = "https://api.open-meteo.com/v1/forecast"
    
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days_back)
    
    for i in range(days_back):
        target_date = (start_date + timedelta(days=i)).strftime('%Y-%m-%d')
        output_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw', 'openmeteo')
        os.makedirs(output_dir, exist_ok=True)
        
        output_file = os.path.join(output_dir, f"{target_date}.json")
        
        if os.path.exists(output_file):
            print(f"Skipping {target_date}, file already exists.")
            continue
            
        daily_results = {}
        total_rows = 0
            
        for city, coords in CITIES.items():
            params = {
                "latitude": coords["lat"],
                "longitude": coords["lon"],
                "start_date": target_date,
                "end_date": target_date,
                "hourly": "temperature_2m,relative_humidity_2m,rain,wind_speed_10m"
            }
            
            try:
                response = requests.get(forecast_url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                data['station'] = city # Inject station for downstream merging
                daily_results[city] = data
                total_rows += len(data.get('hourly', {}).get('time', []))
            except Exception as e:
                print(f"Failed for {city} on {target_date}: {e}")
                
        if daily_results:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(daily_results, f, indent=2)
                
            log_extraction(source=f"openmeteo_{target_date}", status="SUCCESS", row_count=total_rows)
            print(f"Saved {total_rows} records for {target_date} to {output_file}")

if __name__ == "__main__":
    fetch_openmeteo_data()
