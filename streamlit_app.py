# streamlit_app.py
import streamlit as st
import requests
from geopy.distance import geodesic
from datetime import datetime, timedelta
import pandas as pd
import time

# --- Weather API ---
def fetch_weather(lat, lon):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,precipitation,wind_speed_10m,is_day"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get("current", {})
    else:
        return {}

# --- Anomaly Detection ---
def detect_anomalies(tourist, weather):
    anomalies = []
    now = datetime.now()

    # Inactivity
    inactive_minutes = (now - tourist["last_active_time"]).total_seconds() / 60
    if inactive_minutes > 30:
        anomalies.append(f" Prolonged inactivity: {int(inactive_minutes)} minutes")

    # Route Deviation
    expected_loc = tourist["itinerary"]["expected_location"]
    actual_loc = tourist["current_location"]
    distance_from_expected = geodesic(actual_loc, expected_loc).meters
    if distance_from_expected > 300:
        anomalies.append(f" Route Deviation: {int(distance_from_expected)} meters away")

    # GPS Lost
    if not tourist["gps_signal"]:
        if tourist["last_gps_signal_location"]:
            anomalies.append(
                f" GPS Signal Lost near {tourist['last_gps_signal_location']} (tracking last known location)"
            )
        else:
            anomalies.append(" GPS Signal Lost (no last known location available)")

    # Panic Button
    if tourist["panic_button_pressed"]:
        anomalies.append(" Panic button activated!")

    # Weather Risk
    wind_speed = weather.get("wind_speed_10m", 0)
    precipitation = weather.get("precipitation", 0)
    if precipitation > 5 or wind_speed > 15:
        anomalies.append(
            f" Risky weather detected: {precipitation} mm rain, {wind_speed} km/h wind"
        )

    return anomalies


# --- Streamlit UI ---
st.title("Tourist Safety Monitoring Dashboard")

# Sliders for location input
lat = st.slider("Current Latitude", -90.0, 90.0, 27.172, step=0.001)
lon = st.slider("Current Longitude", -180.0, 180.0, 78.042, step=0.001)

# Create a tourist with some defaults
tourist = {
    "tourist_id": "T1001",
    "current_location": (lat, lon),
    "last_known_location": (lat, lon),
    "last_active_time": datetime.now() - timedelta(minutes=15),  # default
    "itinerary": {
        "expected_location": (lat + 0.002, lon + 0.002),  # expected nearby
        "location_type": "monument",
        "time_window_start": datetime.now() - timedelta(hours=1),
        "time_window_end": datetime.now() + timedelta(hours=1)
    },
    "panic_button_pressed": False,
    "gps_signal": True,
    "last_gps_signal_location": None
}

# --- Button to Run Monitoring in cycles ---
if st.button("Run Monitoring"):
    st.write(f"⏰ Monitoring started at {datetime.now().strftime('%H:%M:%S')}")

    for cycle in range(10):  # simulate 3 monitoring cycles
        st.subheader(f" Cycle {cycle+1}")

        weather_data = fetch_weather(*tourist["current_location"])
        anomalies_detected = detect_anomalies(tourist, weather_data)

        st.write(f"👤 Tourist {tourist['tourist_id']} | Location: {tourist['current_location']}")
        st.json(weather_data)

        if anomalies_detected:
            st.error("⚠️ Anomalies Detected:")
            for issue in anomalies_detected:
                st.write(" -", issue)
        else:
            st.success("✅ No anomalies detected. Tourist is safe.")

        # Show location on map
        df = pd.DataFrame([[lat, lon]], columns=["lat", "lon"])
        st.map(df, zoom=12)

        time.sleep(5)  # wait before next cycle
