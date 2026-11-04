import os
import json
from datetime import datetime, timedelta

def create_mocks():
    CITIES = {
        "Los Angeles": 12.0,
        "New York": 9.0,
        "London": 11.0,
        "Tokyo": 14.0,
        "Paris": 13.0,
        "Delhi": 85.0,
        "Beijing": 65.0,
        "Sydney": 8.0,
        "Mumbai": 45.0,
        "Bengaluru": 30.0,
        "Chennai": 35.0,
        "Kolkata": 55.0,
        "Hyderabad": 40.0,
        "Pune": 38.0,
        "Ahmedabad": 50.0
    }
    
    start_date = datetime(2026, 9, 1)
    for i in range(7):
        target_date = (start_date + timedelta(days=i)).strftime('%Y-%m-%d')
        output_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw', 'openaq')
        os.makedirs(output_dir, exist_ok=True)
        
        results = []
        for city, baseline in CITIES.items():
            for hour in range(24):
                dt_str = f"{target_date}T{hour:02d}:00:00Z"
                # Good record
                results.append({
                    "location": city,
                    "parameter": "pm25",
                    "value": baseline + (hour % 10),
                    "unit": "µg/m³",
                    "date": {"utc": dt_str}
                })
                
            # Add some invalid records to test validation
            results.append({
                "location": city,
                "parameter": "pm25",
                "value": -5.0, # Negative
                "unit": "µg/m³",
                "date": {"utc": f"{target_date}T12:00:00Z"}
            })
            results.append({
                "location": city,
                "parameter": "pm25",
                "value": 10000.0, # Outlier
                "unit": "µg/m³",
                "date": {"utc": f"{target_date}T13:00:00Z"}
            })
            # Duplicate
            results.append({
                "location": city,
                "parameter": "pm25",
                "value": baseline + 5.0,
                "unit": "µg/m³",
                "date": {"utc": f"{target_date}T10:00:00Z"}
            })
            
        data = {"results": results}
        output_file = os.path.join(output_dir, f"{target_date}.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

if __name__ == "__main__":
    create_mocks()
