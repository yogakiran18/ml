from fastapi import FastAPI, HTTPException
from serving.schemas import PredictRequest, PredictResponse
import mlflow.sklearn
import pandas as pd
from datetime import datetime
import contextlib
import os

# Global variables for model
model = None
MODEL_VERSION = "2"
MODEL_NAME = "AQI_Predictor_Global"

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    global model
    try:
        # Load bundled model artifact directly from filesystem (stateless container approach)
        model_path = os.path.join(os.path.dirname(__file__), "model_artifact")
        print(f"Loading {MODEL_NAME} version {MODEL_VERSION} from {model_path}...")
        
        # We can still use mlflow.sklearn to deserialize, but pointing to local path
        model = mlflow.sklearn.load_model(model_path)
        print("Model loaded successfully.")
    except Exception as e:
        print(f"Error loading model: {e}")
    yield
    # Cleanup if needed
    print("Shutting down API...")

app = FastAPI(title="AQI Prediction API", version="1.0", lifespan=lifespan)

@app.get("/health")
def health_check():
    return {"status": "ok", "model_loaded": model is not None}

@app.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest):
    if model is None:
        raise HTTPException(status_code=503, detail="Model is not loaded.")
        
    # Convert request to dataframe matching model signature
    input_data = pd.DataFrame([{
        'lag_1_pm25': request.lag_1_pm25,
        'lag_1_temp': request.lag_1_temp,
        'temperature_2m_avg': request.temperature_2m_avg,
        'day_of_week': request.day_of_week,
        'month': request.month
    }])
    
    # One-hot encode the station feature
    # Must match exactly the columns seen during training
    stations = ["Ahmedabad", "Beijing", "Bengaluru", "Chennai", "Delhi", "Hyderabad", "Kolkata", "London", "Los Angeles", "Mumbai", "New York", "Paris", "Pune", "Sydney", "Tokyo"]
    for s in stations:
        input_data[f'station_{s}'] = 0
        
    station_col = f'station_{request.station}'
    if station_col in input_data.columns:
        input_data[station_col] = 1
    
    try:
        prediction = model.predict(input_data)[0]
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Prediction failed: {e}")
        
    # Log the prediction for retrospective performance monitoring
    try:
        from monitoring.performance_log import log_prediction
        features_dict = input_data.iloc[0].to_dict()
        log_prediction(features_dict, float(prediction), MODEL_VERSION)
    except Exception as e:
        print(f"Warning: Failed to log prediction: {e}")
        
    return PredictResponse(
        predicted_pm25=float(prediction),
        model_version=MODEL_VERSION,
        timestamp=datetime.utcnow()
    )
