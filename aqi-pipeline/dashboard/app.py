import streamlit as st
import pandas as pd
import os
import plotly.express as px
import plotly.graph_objects as go
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

st.set_page_config(page_title="Air Quality & Weather Dashboard", layout="wide")
st.title("Air Quality & Weather Dashboard")

@st.cache_data
def load_data():
    import sqlite3
    
    # Connect to the local SQLite fallback since Postgres is unavailable locally
    conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', 'aqi_db.sqlite'))

    # 1. Gold daily table
    query_gold = "SELECT * FROM gold_daily_aqi_by_station ORDER BY date;"
    df_gold = pd.read_sql(query_gold, conn)
    
    # 2. Hourly data for heatmap
    query_hourly = """
        SELECT a.station, a.timestamp, a.value as pm25, m.temperature_2m, m.relative_humidity_2m
        FROM cln_openaq a
        JOIN cln_openmeteo m ON a.station = m.station AND a.timestamp = m.timestamp
        WHERE a.parameter = 'pm25'
    """
    df_hourly = pd.read_sql(query_hourly, conn)
    
    conn.close()
    return df_gold, df_hourly

df_gold, df_hourly = load_data()
st.success("✅ Connected directly to SQLite Gold Layer (`daily_aqi_by_station`).")

st.sidebar.header("Filters")
# List of global cities for demo purposes
global_cities = ["Ahmedabad", "Beijing", "Bengaluru", "Chennai", "Delhi", "Hyderabad", "Kolkata", "London", "Los Angeles", "Mumbai", "New York", "Paris", "Pune", "Sydney", "Tokyo"]
actual_stations = df_gold['station'].unique().tolist()

# Combine lists and remove duplicates
all_stations = actual_stations + [c for c in global_cities if c not in actual_stations]

selected_station = st.sidebar.selectbox("Select Station/City", all_stations)

if selected_station not in actual_stations:
    st.warning(f"⚠️ No data currently available for **{selected_station}**. Please select a city with active ingestion data (e.g., {actual_stations[0] if actual_stations else 'None'}).")
    st.stop()

df_g_filtered = df_gold[df_gold['station'] == selected_station]
df_h_filtered = df_hourly[df_hourly['station'] == selected_station]

col1, col2 = st.columns(2)

# 1. AQI trend over time
with col1:
    st.subheader("1. AQI Trend Over Time (Daily PM2.5)")
    fig1 = px.line(df_g_filtered, x='date', y='pm25_avg', color='aqi_category', markers=True, 
                   title=f"AQI Trend for {selected_station}")
    st.plotly_chart(fig1, use_container_width=True)

# 2. Pollutant contribution breakdown / AQI Category Distribution
with col2:
    st.subheader("2. AQI Category Breakdown")
    category_counts = df_g_filtered['aqi_category'].value_counts().reset_index()
    category_counts.columns = ['aqi_category', 'count']
    fig2 = px.pie(category_counts, names='aqi_category', values='count', 
                  title="Distribution of AQI Categories (7 Days)")
    st.plotly_chart(fig2, use_container_width=True)

col3, col4 = st.columns(2)

# 3. Station/city comparison
with col3:
    st.subheader("3. Station Comparison (Avg PM2.5)")
    station_avg = df_gold.groupby('station')['pm25_avg'].mean().reset_index()
    station_avg = station_avg.sort_values('pm25_avg', ascending=False)
    
    # Highlight selected station
    colors = ['#FF4B4B' if s == selected_station else '#D3D3D3' for s in station_avg['station']]
    borders = ['black' if s == selected_station else 'rgba(0,0,0,0)' for s in station_avg['station']]
    
    fig3 = go.Figure(go.Bar(
        x=station_avg['station'],
        y=station_avg['pm25_avg'],
        marker=dict(color=colors, line=dict(color=borders, width=2)),
        text=station_avg['pm25_avg'].round(1),
        textposition='outside'
    ))
    fig3.update_layout(
        xaxis_tickangle=-45,
        yaxis_title="Avg PM2.5",
        xaxis_title="Station",
        title=f"Selected: {selected_station}",
        showlegend=False
    )
    st.plotly_chart(fig3, use_container_width=True)

# 4. Hourly pattern (heatmap)
with col4:
    st.subheader("4. Hourly PM2.5 Pattern")
    df_h_filtered['hour'] = pd.to_datetime(df_h_filtered['timestamp']).dt.hour
    df_h_filtered['date'] = pd.to_datetime(df_h_filtered['timestamp']).dt.date
    hourly_pivot = df_h_filtered.pivot_table(index='hour', columns='date', values='pm25', aggfunc='mean')
    fig4 = px.imshow(hourly_pivot, labels=dict(x="Date", y="Hour of Day", color="PM2.5"), aspect="auto", 
                     title="Hourly PM2.5 Heatmap")
    st.plotly_chart(fig4, use_container_width=True)

# 5. Weather variable vs AQI
st.subheader("5. Weather vs AQI (Temperature vs PM2.5)")
fig5 = px.scatter(df_g_filtered, x='temperature_2m_avg', y='pm25_avg', color='aqi_category', 
                  size='pm25_avg', hover_data=['date'], title="Temperature vs PM2.5")
st.plotly_chart(fig5, use_container_width=True)
