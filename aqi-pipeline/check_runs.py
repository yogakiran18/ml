import mlflow
mlflow.set_tracking_uri('sqlite:///mlflow/mlflow.db')
client = mlflow.tracking.MlflowClient()
exp = client.get_experiment_by_name('AQI_Prediction')
runs = client.search_runs(exp.experiment_id)
print('Runs found:', len(runs))
for r in runs:
    name = r.data.tags.get("mlflow.runName")
    rmse = r.data.metrics.get("rmse")
    mae = r.data.metrics.get("mae")
    print(f"Run: {name} | RMSE: {rmse} | MAE: {mae}")
