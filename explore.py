import requests
import pandas as pd

BASE_URL = "https://api.openf1.org/v1"


def get_data(endpoint, **params):
    """Fetch data from an OpenF1 endpoint and return it as a DataFrame."""
    response = requests.get(f"{BASE_URL}/{endpoint}", params=params, timeout=30)
    response.raise_for_status()  # stop with a clear error if the request failed
    return pd.DataFrame(response.json())


# 1. Find the 2024 Italian Grand Prix race session
sessions = get_data("sessions", year=2024, country_name="Italy", session_name="Race")
print(sessions[["session_key", "location", "date_start"]])

session_key = sessions["session_key"].iloc[0]

# 2. Get every lap and every tyre stint in that race
laps = get_data("laps", session_key=session_key)
stints = get_data("stints", session_key=session_key)

print(laps[["driver_number", "lap_number", "lap_duration", "is_pit_out_lap"]].head(20))
print(stints[["driver_number", "stint_number", "compound", "lap_start", "lap_end"]].head(20))