-- 1. STAGING TABLES (One per source)
CREATE TABLE IF NOT EXISTS stg_openaq (
    location VARCHAR(255),
    parameter VARCHAR(50),
    value NUMERIC(10, 2),
    unit VARCHAR(50),
    date_utc TIMESTAMP
);

CREATE TABLE IF NOT EXISTS stg_openmeteo (
    time TIMESTAMP,
    temperature_2m NUMERIC(10, 2),
    relative_humidity_2m NUMERIC(10, 2),
    rain NUMERIC(10, 2),
    wind_speed_10m NUMERIC(10, 2)
);

-- 2. CLEANED TABLES
CREATE TABLE IF NOT EXISTS cln_openaq (
    station VARCHAR(255),
    timestamp TIMESTAMP,
    parameter VARCHAR(50),
    value NUMERIC(10, 2),
    unit VARCHAR(50),
    PRIMARY KEY (station, timestamp, parameter)
);

CREATE TABLE IF NOT EXISTS cln_openmeteo (
    station VARCHAR(255),
    timestamp TIMESTAMP,
    temperature_2m NUMERIC(10, 2),
    relative_humidity_2m NUMERIC(10, 2),
    rain NUMERIC(10, 2),
    wind_speed_10m NUMERIC(10, 2),
    PRIMARY KEY (station, timestamp)
);

-- 3. GOLD ANALYTICAL TABLE
CREATE TABLE IF NOT EXISTS gold_daily_aqi_by_station (
    station VARCHAR(255),
    date DATE,
    pm25_avg NUMERIC(10, 2),
    temperature_2m_avg NUMERIC(10, 2),
    aqi_category VARCHAR(50),
    PRIMARY KEY (station, date)
);
