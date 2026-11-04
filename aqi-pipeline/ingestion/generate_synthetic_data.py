import os
import json
import random
import math
from datetime import datetime, timedelta

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

def generate_data(days=365, start_year=2025, start_month=1, start_day=1):
    start_date = datetime(start_year, start_month, start_day)
    
    openaq_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw', 'openaq')
    openmeteo_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw', 'openmeteo')
    os.makedirs(openaq_dir, exist_ok=True)
    os.makedirs(openmeteo_dir, exist_ok=True)
    
    for day_offset in range(days):
        target_date = start_date + timedelta(days=day_offset)
        target_date_str = target_date.strftime('%Y-%m-%d')
        
        # Calculate seasonal factor (0 to 1)
        # Peak winter pollution in northern hemisphere ~ Jan (day 0) or Dec (day 365)
        # We'll use a simple cosine wave.
        day_of_year = target_date.timetuple().tm_yday
        seasonal_factor = (math.cos((day_of_year - 15) * 2 * math.pi / 365) + 1) / 2
        
        openaq_results = []
        openmeteo_daily = {}
        
        for city, baseline in CITIES.items():
            # Adjust seasonal factor for southern hemisphere (Sydney)
            if city == "Sydney":
                city_seasonal_factor = 1.0 - seasonal_factor
            else:
                city_seasonal_factor = seasonal_factor
                
            city_baseline = baseline * (0.6 + 0.8 * city_seasonal_factor)
            
            hourly_times = []
            hourly_temps = []
            hourly_rh = []
            hourly_rain = []
            hourly_wind = []
            
            for hour in range(24):
                dt_str_openaq = f"{target_date_str}T{hour:02d}:00:00Z"
                dt_str_meteo = f"{target_date_str}T{hour:02d}:00"
                
                # Temperature cycle: coolest at 4 AM, hottest at 3 PM (15:00)
                temp_baseline = 15.0 if city_seasonal_factor > 0.5 else 25.0
                if city in ["Delhi", "Mumbai", "Chennai", "Bengaluru", "Kolkata", "Hyderabad", "Pune", "Ahmedabad"]:
                    temp_baseline += 10.0 # Hotter in India
                
                temp_variation = -5.0 * math.cos((hour - 4) * 2 * math.pi / 24)
                temp = temp_baseline + temp_variation + random.uniform(-1, 1)
                
                # PM2.5 cycle: peak at 8 AM and 8 PM (traffic)
                traffic_factor = 0.3 * (math.exp(-0.5 * ((hour - 8)/2)**2) + math.exp(-0.5 * ((hour - 20)/2)**2))
                
                # Weather correlation: rain washes away PM2.5, wind disperses it
                is_raining = random.random() < 0.1
                rain = random.uniform(1.0, 5.0) if is_raining else 0.0
                wind = random.uniform(2.0, 15.0)
                
                pm25 = city_baseline * (1.0 + traffic_factor)
                if rain > 0:
                    pm25 *= 0.5
                pm25 *= (10.0 / (wind + 5.0)) # Higher wind -> lower pm25
                
                pm25 += random.uniform(-0.1 * pm25, 0.1 * pm25) # noise
                pm25 = max(0.1, pm25)
                
                # OpenAQ
                openaq_results.append({
                    "location": city,
                    "parameter": "pm25",
                    "value": round(pm25, 2),
                    "unit": "µg/m³",
                    "date": {"utc": dt_str_openaq}
                })
                
                # OpenMeteo
                hourly_times.append(dt_str_meteo)
                hourly_temps.append(round(temp, 1))
                hourly_rh.append(random.randint(40, 90))
                hourly_rain.append(round(rain, 1))
                hourly_wind.append(round(wind, 1))
                
            openmeteo_daily[city] = {
                "hourly": {
                    "time": hourly_times,
                    "temperature_2m": hourly_temps,
                    "relative_humidity_2m": hourly_rh,
                    "rain": hourly_rain,
                    "wind_speed_10m": hourly_wind
                },
                "station": city
            }
            
        # Save OpenAQ
        with open(os.path.join(openaq_dir, f"{target_date_str}.json"), 'w', encoding='utf-8') as f:
            json.dump({"results": openaq_results}, f, indent=2)
            
        # Save OpenMeteo
        with open(os.path.join(openmeteo_dir, f"{target_date_str}.json"), 'w', encoding='utf-8') as f:
            json.dump(openmeteo_daily, f, indent=2)
            
        if day_offset % 30 == 0:
            print(f"Generated {day_offset} days...")
            
    print(f"Generated {days} days of synthetic data.")

if __name__ == "__main__":
    generate_data()
