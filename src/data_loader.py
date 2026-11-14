# The goal is to create a data loader and store into cache.
# So when user ask a question about a race it will first check the existing cache data before pulling the dataset from API

import json
import unicodedata
from pathlib import Path

import pandas as pd
import requests

BASE_URL="https://api.openf1.org/v1"

# The cache folder, worked out from where THIS file lives,
# so it works no matter which folder you run Python from
CACHE_DIR = Path(__file__).parent.parent / "data" / "cache"

# Data only valid from 2023
FIRST_OPENF1_YEAR =2023

def fetch_json(endpoint, **params):
    #Fetch raw data from OpenF1. Returns a list of dictionaries.
    response = requests.get(f"{BASE_URL}/{endpoint}", params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def _normalise(text):
    #Lowercase and strip accents, so "montreal" matches "Montréal"
    decomposed = unicodedata.normalize("NFKD", text)
    without_accents = "".join(c for c in decomposed if not unicodedata.combining(c))
    return without_accents.strip().lower()


def find_session_key(year, location):
    """Find the session key for a race, e.g. (2024, "Monza")."""
    # Fetch every race in the season (not filtered by location), so we can
    # match the location ourselves and list valid options if it isn't found.

    if year<FIRST_OPENF1_YEAR:
            raise ValueError(f"No race data found for {year}. OpenF1 only has data from 2023 onwards.")
    try:
        sessions = fetch_json("sessions", year=year, session_name="Race")
    except requests.HTTPError as err:
        # OpenF1 answers "no results" with a 404 rather than an empty list
        if err.response is not None and err.response.status_code == 404:
            sessions = []
        else:
            raise #display ori error message

    if not sessions:
        raise ValueError(f"No race data is found for {year} yet")

    wanted = _normalise(location)
    for session in sessions:
        if _normalise(session["location"]) == wanted:
            return session["session_key"]

    available = ", ".join(sorted(s["location"] for s in sessions))
    raise ValueError(f"No race found at '{location}' in {year}. Available locations: {available}")


def get_cached(endpoint, session_key):
    #Get one endpoint's data for a session, using the cache when possible."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / f"{endpoint}_{session_key}.json"

    data = None
    if cache_file.exists():
        try:
            with open(cache_file, "r", encoding="utf-8") as file:
                data=json.load(file)
        except json.JSONDecodeError:
            data = None  # corrupted cache file: fall through and re-fetch

    if data is None:
        data = fetch_json(endpoint, session_key=session_key)
        with open(cache_file, "w", encoding="utf-8") as file:
            json.dump(data, file)

    return pd.DataFrame(data)


def load_race(year, location):
    """Load everything we need for one race. Returns a dict of DataFrames."""
    session_key = find_session_key(year, location)

    # TODO 4: return a dictionary with these keys, each using get_cached:
    #   "laps", "stints", "pit", "race_control", "drivers",
    #   "session_result", "position", "intervals"
    # (the dictionary key and the endpoint name are the same)
    data ={
        "laps":get_cached("laps", session_key=session_key), 
        "stints": get_cached("stints", session_key=session_key),
        "race_control":get_cached("race_control", session_key=session_key),
        "pit":get_cached("pit", session_key=session_key),
        "drivers": get_cached("drivers", session_key=session_key),
        "session_result": get_cached("session_result", session_key=session_key),
        "position": get_cached("position", session_key=session_key),
        "intervals": get_cached("intervals", session_key=session_key)
    }
    return data

if __name__ == "__main__":
    print(CACHE_DIR)
    race = load_race(2024, "Monza")
    for name, table in race.items():
        print(f"{name}: {len(table)} rows")


