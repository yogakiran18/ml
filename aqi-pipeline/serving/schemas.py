from pydantic import BaseModel
from datetime import datetime

class PredictRequest(BaseModel):
    station: str
    lag_1_pm25: float
    lag_1_temp: float
    temperature_2m_avg: float
    day_of_week: int
    month: int

class PredictResponse(BaseModel):
    predicted_pm25: float
    model_version: str
    timestamp: datetime
