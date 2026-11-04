# Model Lifecycle & Governance

This document outlines the operational policies for the AQI Predictor model, including when it should be retrained, how it is promoted through environments, and how we handle failures in production.

## 1. Retraining Criteria
The model is **not** retrained manually "as needed". Instead, it follows a strict automated retraining policy triggered by either of the following two concrete criteria:

1. **Performance Degradation**: Retraining is automatically triggered if the rolling 7-day Mean Absolute Error (MAE) calculated in `prediction_logs` exceeds **5.0 AQI points**. 
2. **Feature Drift**: The `monitoring/drift_check.py` script runs daily. If the Kolmogorov-Smirnov (KS) test yields a p-value `< 0.05` for any of the core meteorological features (`lag_1_pm25`, `lag_1_temp`, `temperature_2m_avg`) across a 14-day rolling window compared to the training baseline, a retrain is triggered.

## 2. Model Promotion (Staging to Production)
We utilize the MLflow Model Registry to manage the lifecycle of our trained artifacts.
- **Registration**: When a retraining job completes successfully, the resulting model artifact is registered into MLflow as a new version under the `AQI_Predictor_LA` model name. By default, it is placed in the **"Staging"** stage.
- **Evaluation**: The new "Staging" model is run against the holdout test set via `models/evaluate.py`. 
- **Promotion**: If the new model's RMSE is lower than the current "Production" model's RMSE on the same benchmark dataset, the MLflow API is used to transition the new model to **"Production"** and the previous model to **"Archived"**.

## 3. Rollback Plan
If a newly deployed model severely underperforms or introduces latency/memory issues in the FastAPI serving layer, the following rollback protocol is executed:
1. **Container Reversion**: Because our serving Docker image statically bundles the model artifact at build time (`serving/Dockerfile`), rolling back the live API simply involves tearing down the current container and spinning up the previously tagged Docker image (e.g., `docker run aqi-serve:v1.2` instead of `v1.3`).
2. **Registry Reversion**: In MLflow, the failing version is manually transitioned to the **"Archived"** state, and the previous known-good version is transitioned back to **"Production"**.

## 4. Known Limitations
Based on the initial automated evaluation and error analysis report, the current Linear Regression baseline model has a few documented weaknesses:
1. **Sudden Meteorological Shifts**: The model relies on simple 1-day lags (`lag_1_temp`). It fails to capture sudden, same-day temperature drops or wind pattern changes.
2. **External Anomalies**: It lacks features to account for sudden external pollutant spikes (e.g., local wildfires or traffic accidents). When the actual AQI spikes rapidly independent of the previous day's data, the model heavily underestimates the value.
3. **Data Volume**: The current mock environment utilizes an extremely limited dataset, meaning the model's complexity is artificially restricted to prevent immediate overfitting in production.
