import mlflow
from mlflow.artifacts import download_artifacts
import os
import shutil

def download():
    # Set tracking URI to local db
    mlflow.set_tracking_uri("sqlite:///mlflow/mlflow.db")
    model_name = "AQI_Predictor_Global"
    model_version = "2"
    
    print(f"Locating {model_name} version {model_version} in MLflow...")
    model_uri = f"models:/{model_name}/{model_version}"
    
    local_dir = "serving/model_artifact"
    if os.path.exists(local_dir):
        shutil.rmtree(local_dir)
    
    print(f"Downloading artifact to {local_dir}...")
    # This downloads the raw model directory containing the MLmodel file and the pickled scikit-learn model
    download_artifacts(artifact_uri=model_uri, dst_path=local_dir)
    print("Download complete.")

if __name__ == '__main__':
    download()
