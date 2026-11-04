# AQI Data Engineering Pipeline

An end-to-end Air Quality Index (AQI) data engineering pipeline that extracts environmental data from the OpenAQ and OpenMeteo APIs, validates and transforms it through an ETL process, and loads it into a PostgreSQL data warehouse to be visualized on a Streamlit dashboard.

---

## 🏗 Setup Instructions

To get this project up and running from scratch, follow these instructions. 

### 1. Prerequisites
Ensure you have the following installed on your machine:
- **Docker** and **Docker Compose**
- **Python 3.10+** (if running the dashboard locally outside of Docker)

### 2. Environment Configuration
Create the environment file required by the services. 
1. Copy the provided `.env.example` file to create a new `.env` file in the `aqi-pipeline` root directory.
   ```bash
   cp .env.example .env
   ```
2. Open the `.env` file and insert your API keys (e.g., `OPENAQ_API_KEY`). The default PostgreSQL credentials (`POSTGRES_USER=postgres`, `POSTGRES_PASSWORD=postgres`, `POSTGRES_DB=aqi_db`) should work out of the box.

### 3. Start the Infrastructure
The pipeline relies on PostgreSQL for the data warehouse and Apache Airflow for orchestration. Start these services using Docker Compose:
```bash
docker-compose up -d
```
This command will pull the necessary images and spin up the `aqi_postgres` and `aqi_airflow` containers.

### 4. Triggering the ETL DAG
The ETL pipeline is orchestrated by Airflow and runs daily by default. To trigger it manually for the first time:

**Option A: Using the Airflow UI**
1. Navigate to `http://localhost:8080` in your browser.
2. Log in (default username: `admin`, password: `admin` — check Airflow logs if this changes, though it is configured to run `standalone`).
3. Find the `aqi_pipeline` DAG in the list.
4. Toggle the DAG to **Unpause** (turn the switch on).
5. Click the **Trigger DAG** (Play) button to run the pipeline immediately.

**Option B: Using Airflow CLI**
Run the following command inside the Airflow container to trigger the DAG:
```bash
docker exec -it aqi_airflow airflow dags trigger aqi_pipeline
```

You can monitor the progress of the Extract, Validate, Clean, Transform, and Load tasks in the Airflow UI.

### 5. Launching the Dashboard
Once the DAG has successfully completed and loaded data into the PostgreSQL `daily_aqi_by_station` table, you can view the analytics dashboard.

If you have Python installed locally:
1. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the Streamlit application:
   ```bash
   streamlit run dashboard/app.py
   ```
3. Open `http://localhost:8501` in your browser to view the interactive Air Quality dashboard.

---

## 📚 Documentation
- **[Data Dictionary](docs/data_dictionary.md)**: Contains schema, source, and validation rule details for staging, cleaned, and gold tables.
- **[Architecture Diagram](docs/architecture_diagram.png)**: Visualizes the pipeline data flow from Source APIs to the Dashboard.
