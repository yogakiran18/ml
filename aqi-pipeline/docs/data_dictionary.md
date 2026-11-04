# AQI Pipeline Data Dictionary

This document details the schema, sources, units, and validation rules for tables across the Staging, Cleaned, and Gold layers of the AQI pipeline.

---

## 1. Staging Layer

Raw data ingested from APIs, lightly validated before insertion.

### Table: `stg_openaq`
**Source:** OpenAQ API (`GET /v2/measurements`)

| Column | Data Type | Unit | Description | Validation Rule |
| :--- | :--- | :--- | :--- | :--- |
| `location` | VARCHAR(255) | - | Name of the monitoring station | - |
| `parameter` | VARCHAR(50) | - | Pollutant measured (e.g., pm25, no2) | - |
| `value` | NUMERIC(10, 2) | Various | The recorded measurement | Must be between `0` and `5000` |
| `unit` | VARCHAR(50) | - | Unit of measurement | - |
| `date_utc` | TIMESTAMP | - | UTC time of measurement | Duplicate records (location, date_utc, parameter) rejected |

### Table: `stg_openmeteo`
**Source:** OpenMeteo API (Historical Weather)

| Column | Data Type | Unit | Description | Validation Rule |
| :--- | :--- | :--- | :--- | :--- |
| `time` | TIMESTAMP | - | UTC time of measurement | Duplicate records (time) rejected |
| `temperature_2m` | NUMERIC(10, 2) | °C | Air temperature at 2m above ground | - |
| `relative_humidity_2m` | NUMERIC(10, 2) | % | Relative humidity at 2m above ground | Must be between `0` and `100` |
| `rain` | NUMERIC(10, 2) | mm | Rain volume | - |
| `wind_speed_10m` | NUMERIC(10, 2) | km/h | Wind speed at 10m above ground | - |

---

## 2. Cleaned Layer

Data from staging that has been normalized and standardized.

### Table: `cln_openaq`
| Column | Data Type | Unit | Description | Transformation/Validation |
| :--- | :--- | :--- | :--- | :--- |
| `station` | VARCHAR(255) | - | Standardized station name | Title-cased and stripped of whitespace from `location` |
| `timestamp` | TIMESTAMP | - | Naive UTC timestamp | Converted to naive timezone-unaware UTC from `date_utc` |
| `parameter` | VARCHAR(50) | - | Pollutant measured | - |
| `value` | NUMERIC(10, 2) | Various | The recorded measurement | - |
| `unit` | VARCHAR(50) | - | Standardized unit | Replaced `ug/m3` with `µg/m³` |

*(Primary Key: `station, timestamp, parameter`)*

### Table: `cln_openmeteo`
| Column | Data Type | Unit | Description | Transformation/Validation |
| :--- | :--- | :--- | :--- | :--- |
| `station` | VARCHAR(255) | - | Assigned station name | Hardcoded as `"Los Angeles"` to match OpenAQ mapping |
| `timestamp` | TIMESTAMP | - | Naive UTC timestamp | Converted to naive timezone-unaware UTC from `time` |
| `temperature_2m` | NUMERIC(10, 2) | °C | Air temperature at 2m | - |
| `relative_humidity_2m` | NUMERIC(10, 2) | % | Relative humidity at 2m | - |
| `rain` | NUMERIC(10, 2) | mm | Rain volume | - |
| `wind_speed_10m` | NUMERIC(10, 2) | km/h | Wind speed at 10m | - |

*(Primary Key: `station, timestamp`)*

---

## 3. Gold Analytical Layer

Aggregated, analytics-ready tables for dashboards and reporting.

### Table: `daily_aqi_by_station` (mapped from `gold_daily_aqi_by_station`)
| Column | Data Type | Unit | Description | Transformation/Validation |
| :--- | :--- | :--- | :--- | :--- |
| `station` | VARCHAR(255) | - | Standardized station name | Joined from `cln_openaq` & `cln_openmeteo` |
| `date` | DATE | - | Local day of aggregation | Extracted date from UTC `timestamp` |
| `pm25_avg` | NUMERIC(10, 2) | µg/m³ | Daily mean PM2.5 | Aggregated (`MEAN`) across hourly readings |
| `temperature_2m_avg` | NUMERIC(10, 2) | °C | Daily mean temperature | Aggregated (`MEAN`) across hourly readings |
| `aqi_category` | VARCHAR(50) | - | EPA Air Quality Index Category | Derived using US EPA Breakpoints for `pm25_avg` |

*(Primary Key: `station, date`)*
