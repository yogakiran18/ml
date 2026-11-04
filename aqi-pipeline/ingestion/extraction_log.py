import csv
import os
from datetime import datetime, timezone

LOG_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'extraction_log.csv')

def log_extraction(source: str, status: str, row_count: int, error_message: str = None):
    # Ensure directory exists
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    
    file_exists = os.path.isfile(LOG_FILE)
    
    with open(LOG_FILE, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['timestamp', 'source', 'status', 'row_count', 'error_message'])
            
        timestamp = datetime.now(timezone.utc).isoformat()
        writer.writerow([timestamp, source, status, row_count, error_message or ""])
