import sqlite3
import pandas as pd
from scipy import stats

def check_drift():
    """
    Checks for data drift using the Kolmogorov-Smirnov (KS) test.
    We use the KS test because it is lightweight, requires no heavy external dependencies (like Evidently),
    and is standard for comparing two continuous univariate distributions to see if they differ significantly.
    """
    # Load feature data
    conn = sqlite3.connect('aqi_db.sqlite')
    query = "SELECT lag_1_pm25, lag_1_temp, temperature_2m_avg FROM ml_features ORDER BY date ASC"
    df = pd.read_sql_query(query, conn)
    conn.close()

    if len(df) < 4:
        print("Not enough data to split for drift checking (need at least 4 rows).")
        return

    # Split data chronologically to simulate 'reference' (training) vs 'current' (incoming) data
    split_idx = len(df) // 2
    reference_data = df.iloc[:split_idx]
    current_data = df.iloc[split_idx:]
    
    print(f"--- Data Drift Report (KS Test) ---")
    print(f"Reference period samples: {len(reference_data)}")
    print(f"Current period samples: {len(current_data)}")
    print("-" * 35)

    drift_detected = False
    p_value_threshold = 0.05

    for feature in df.columns:
        ref_values = reference_data[feature].dropna()
        curr_values = current_data[feature].dropna()

        # KS test: null hypothesis is that the two samples are drawn from the same distribution
        statistic, p_value = stats.ks_2samp(ref_values, curr_values)
        
        has_drifted = p_value < p_value_threshold
        if has_drifted:
            drift_detected = True

        status = "DRIFT DETECTED" if has_drifted else "No Drift"
        
        print(f"Feature: {feature}")
        print(f"  P-Value: {p_value:.4f}")
        print(f"  Status:  {status}")
        print("-" * 35)

    if drift_detected:
        print("\nWARNING: Drift detected in one or more features. Model retraining may be required.")
    else:
        print("\nSUCCESS: No significant drift detected.")

if __name__ == '__main__':
    check_drift()
