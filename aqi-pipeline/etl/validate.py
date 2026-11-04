import os
import glob
import json
import pandas as pd

RAW_OPENAQ_DIR = "data/raw/openaq"
RAW_OPENMETEO_DIR = "data/raw/openmeteo"
REJECTED_DIR = "data/rejected"
STAGING_DIR = "data/staging"

def validate_openaq():
    files = glob.glob(f"{RAW_OPENAQ_DIR}/*.json")
    for file in files:
        date_str = os.path.basename(file).split('.')[0]
        with open(file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        results = data.get('results', [])
        if not results:
            print(f"OpenAQ {date_str}: 0 in, 0 rejected, 0 out.")
            continue
            
        df = pd.json_normalize(results)
        if 'date.utc' in df.columns:
            df['date_utc'] = df['date.utc']
        else:
            df['date_utc'] = None
            
        df['reason'] = ""
        
        # Validation rules
        df.loc[df['value'] < 0, 'reason'] += "Negative value; "
        df.loc[df['value'] > 5000, 'reason'] += "Outlier value; "
        
        dup_mask = df.duplicated(subset=['location', 'date_utc', 'parameter'], keep='first')
        df.loc[dup_mask, 'reason'] += "Duplicate record; "
        
        rejected = df[df['reason'] != ""]
        valid = df[df['reason'] == ""]
        
        if not rejected.empty:
            os.makedirs(REJECTED_DIR, exist_ok=True)
            rejected.to_csv(f"{REJECTED_DIR}/openaq_rejected_{date_str}.csv", index=False)
            
        if not valid.empty:
            os.makedirs(STAGING_DIR, exist_ok=True)
            valid.drop(columns=['reason']).to_csv(f"{STAGING_DIR}/openaq_valid_{date_str}.csv", index=False)
            
        print(f"OpenAQ {date_str}: {len(df)} in, {len(rejected)} rejected, {len(valid)} out.")

def validate_openmeteo():
    files = glob.glob(f"{RAW_OPENMETEO_DIR}/*.json")
    for file in files:
        date_str = os.path.basename(file).split('.')[0]
        with open(file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # New structure: {"City Name": {"hourly": {...}}, "City Name 2": {...}}
        all_valid = []
        all_rejected = []
        
        for city, city_data in data.items():
            hourly = city_data.get('hourly', {})
            if not hourly:
                continue
                
            df = pd.DataFrame(hourly)
            df['reason'] = ""
            df['station'] = city  # Propagate the station name
            
            if 'relative_humidity_2m' in df.columns:
                df.loc[(df['relative_humidity_2m'] < 0) | (df['relative_humidity_2m'] > 100), 'reason'] += "Invalid humidity; "
                
            dup_mask = df.duplicated(subset=['time', 'station'], keep='first')
            df.loc[dup_mask, 'reason'] += "Duplicate record; "
            
            rejected = df[df['reason'] != ""]
            valid = df[df['reason'] == ""]
            
            all_rejected.append(rejected)
            all_valid.append(valid)
            
        if all_rejected:
            rejected_df = pd.concat(all_rejected, ignore_index=True)
            if not rejected_df.empty:
                os.makedirs(REJECTED_DIR, exist_ok=True)
                rejected_df.to_csv(f"{REJECTED_DIR}/openmeteo_rejected_{date_str}.csv", index=False)
                
        if all_valid:
            valid_df = pd.concat(all_valid, ignore_index=True)
            if not valid_df.empty:
                os.makedirs(STAGING_DIR, exist_ok=True)
                valid_df.drop(columns=['reason']).to_csv(f"{STAGING_DIR}/openmeteo_valid_{date_str}.csv", index=False)
                print(f"OpenMeteo {date_str}: {len(valid_df) + (len(rejected_df) if all_rejected and not rejected_df.empty else 0)} in, {len(rejected_df) if all_rejected and not rejected_df.empty else 0} rejected, {len(valid_df)} out.")

if __name__ == "__main__":
    print("--- VALIDATION ---")
    validate_openaq()
    validate_openmeteo()
