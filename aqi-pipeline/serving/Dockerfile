FROM python:3.10-slim

WORKDIR /app

# Copy the lean requirements file and install
COPY serving/requirements_serve.txt .
RUN pip install --no-cache-dir -r requirements_serve.txt

# Copy the entire serving directory (includes main.py, schemas.py, and the model_artifact)
COPY serving/ ./serving/

# Expose the API port
EXPOSE 80

# Command to run the uvicorn server
CMD ["uvicorn", "serving.main:app", "--host", "0.0.0.0", "--port", "80"]
