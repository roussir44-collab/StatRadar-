
import streamlit as st
import requests

st.set_page_config(page_title="StatRadar AI", page_icon="⚽", layout="wide")

API_TOKEN = st.secrets["FOOTBALL_DATA_API_KEY"]
BASE_URL = "https://api.football-data.org/v4"
HEADERS = {"X-Auth-Token": API_TOKEN}

st.title("⚽ StatRadar AI")
st.write("Testing football-data.org connection...")

try:
    response = requests.get(f"{BASE_URL}/matches", headers=HEADERS, timeout=20)
    response.raise_for_status()
    data = response.json()
    matches = data.get("matches", [])

    st.success(f"API connected successfully. Matches found: {len(matches)}")

    for match in matches[:10]:
        home = match.get("homeTeam", {}).get("name", "Unknown")
        away = match.get("awayTeam", {}).get("name", "Unknown")
        status = match.get("status", "UNKNOWN")
        st.write(f"{home} vs {away} - {status}")

except Exception as e:
    st.error(f"Error: {e}")
