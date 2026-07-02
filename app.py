import streamlit as st
import requests
from datetime import datetime

st.set_page_config(page_title="StatRadar AI", page_icon="⚽", layout="wide")

API_TOKEN = st.secrets["FOOTBALL_DATA_API_KEY"]
BASE_URL = "https://api.football-data.org/v4"
HEADERS = {"X-Auth-Token": API_TOKEN}

st.markdown("""
    <style>
    .match-card {
        background: #f7f9fc;
        border: 1px solid #e6eaf1;
        border-radius: 16px;
        padding: 18px;
        margin-bottom: 16px;
    }
    .small-muted {
        color: #6b7280;
        font-size: 14px;
    }
    .team-line {
        font-size: 22px;
        font-weight: 700;
        margin-bottom: 8px;
    }
    .section-title {
        font-size: 28px;
        font-weight: 800;
        margin-bottom: 8px;
    }
    </style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=300)
def api_get(endpoint, params=None):
    response = requests.get(f"{BASE_URL}{endpoint}", headers=HEADERS, params=params, timeout=20)
    response.raise_for_status()
    return response.json()

@st.cache_data(ttl=300)
def get_today_matches():
    data = api_get("/matches")
    return data.get("matches", [])

@st.cache_data(ttl=1800)
def get_team_finished_matches(team_id, limit=6):
    data = api_get(f"/teams/{team_id}/matches", params={"status": "FINISHED", "limit": limit})
    return data.get("matches", [])

@st.cache_data(ttl=1800)
def get_competition_standings(comp_code):
    if not comp_code:
        return []
    data = api_get(f"/competitions/{comp_code}/standings")
    standings = data.get("standings", [])
    if standings:
        return standings[0].get("table", [])
    return []

def format_time(utc_date):
    try:
        dt = datetime.fromisoformat(utc_date.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M UTC")
    except:
        return utc_date

def extract_team_form(matches, team_id):
    played = 0
    wins = draws = losses = 0
    goals_for = goals_against = 0

    for m in matches:
        home_id = m.get("homeTeam", {}).get("id")
        away_id = m.get("awayTeam", {}).get("id")
        full = m.get("score", {}).get("fullTime", {})
        hg = full.get("home")
        ag = full.get("away")

        if hg is None or ag is None:
            continue

        if home_id == team_id:
            gf, ga = hg, ag
        elif away_id == team_id:
            gf, ga = ag, hg
        else:
            continue

        played += 1
        goals_for += gf
        goals_against += ga

        if gf > ga:
            wins += 1
        elif gf == ga:
            draws += 1
        else:
            losses += 1

    avg_for = goals_for / played if played else 0
    avg_against = goals_against / played if played else 0
    form_points = wins * 3 + draws

    return {
        "played": played,
        "wins": wins,
        "draws": draws,
        "losses": losses,
        "goals_for": goals_for,
        "goals_against": goals_against,
        "avg_for": avg_for,
        "avg_against": avg_against,
        "form_points": form_points
    }

def get_position(standings_table, team_id):
    for row in standings_table:
        team = row.get("team", {})
        if team.get("id") == team_id:
            return row.get("position"), row.get("points"), row.get("goalDifference")
    return None, None, None

def analyze_match(match):
    home = match.get("homeTeam", {})
    away = match.get("awayTeam", {})
    competition = match.get("competition", {})

    home_id = home.get("id")
    away_id = away.get("id")
    comp_code = competition.get("code")

    home_matches = get_team_finished_matches(home_id, limit=6)
    away_matches = get_team_finished_matches(away_id, limit=6)
    standings = get_competition_standings(comp_code)

    home_form = extract_team_form(home_matches, home_id)
    away_form = extract_team_form(away_matches, away_id)

    home_pos, home_pts, home_gd = get_position(standings, home_id)
    away_pos, away_pts, away_gd = get_position(standings, away_id)

    home_strength = (
        home_form["form_points"] * 1.8
        + home_form["avg_for"] * 2.2
        - home_form["avg_against"] * 1.3
        + 1.2
    )
    away_strength = (
        away_form["form_points"] * 1.8
        + away_form["avg_for"] * 2.2
        - away_form["avg_against"] * 1.3
    )

    if home_pos and away_pos:
        if home_pos < away_pos:
            home_strength += 1.0
        elif away_pos < home_pos:
            away_strength += 1.0

    if home_gd is not None:
        home_strength += home_gd * 0.03
    if away_gd is not None:
        away_strength += away_gd * 0.03

    total = max(home_strength + away_strength, 0.1)
    home_prob = max(5, min(80, round((home_strength / total) * 100)))
    away_prob = max(5, min(80, round((away_strength / total) * 100)))
    draw_prob = max(10, 100 - home_prob - away_prob)

    total_goals_signal = home_form["avg_for"] + away_form["avg_for"]
    defensive_signal = home_form["avg_against"] + away_form["avg_against"]

    if total_goals_signal >= 2.6 or defensive_signal >= 2.4:
        goals_pick = "Over 1.5 goals looks strong"
    elif total_goals_signal >= 1.8:
        goals_pick = "Over 1.5 goals looks possible"
    else:
        goals_pick = "Under 3.5 goals looks safer"

    if home_prob > away_prob + 8:
        winner_pick = f"{home.get('name')} has the edge"
    elif away_prob > home_prob + 8:
        winner_pick = f"{away.get('name')} has the edge"
    else:
        winner_pick = "Match looks balanced"

    confidence = min(88, max(55, abs(home_prob - away_prob) + 52))

    return {
        "winner_pick": winner_pick,
        "goals_pick": goals_pick,
        "home_prob": home_prob,
        "draw_prob": draw_prob,
        "away_prob": away_prob,
        "confidence": confidence,
        "home_form": home_form,
        "away_form": away_form,
        "home_pos": home_pos,
        "away_pos": away_pos,
        "home_pts": home_pts,
        "away_pts": away_pts
    }

st.markdown('<div class="section-title">⚽ StatRadar AI</div>', unsafe_allow_html=True)
st.caption("Today matches + real data-based analysis")

try:
    matches = get_today_matches()

    if not matches:
        st.warning("No matches found today.")
    else:
        st.success(f"API connected successfully. Matches found: {len(matches)}")

        for match in matches:
            home = match.get("homeTeam", {}).get("name", "Unknown")
            away = match.get("awayTeam", {}).get("name", "Unknown")
            competition = match.get("competition", {}).get("name", "Unknown Competition")
            utc_date = format_time(match.get("utcDate", ""))
            status = match.get("status", "UNKNOWN")

            st.markdown('<div class="match-card">', unsafe_allow_html=True)
            st.markdown(f'<div class="team-line">{home} vs {away}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="small-muted">Competition: {competition}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="small-muted">Kickoff: {utc_date}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="small-muted">Status: {status}</div>', unsafe_allow_html=True)

            if st.button("Analyze", key=f"analyze_{match.get('id')}"):
                analysis = analyze_match(match)

                st.info(f"Prediction confidence: {analysis['confidence']}%")
                st.write(f"**Match view:** {analysis['winner_pick']}")
                st.write(f"**Goals view:** {analysis['goals_pick']}")
                st.write(
                    f"**Probabilities:** Home {analysis['home_prob']}% | "
                    f"Draw {analysis['draw_prob']}% | Away {analysis['away_prob']}%"
                )

                st.write("**Recent form:**")
                st.write(
                    f"- Home: {analysis['home_form']['wins']}W / "
                    f"{analysis['home_form']['draws']}D / {analysis['home_form']['losses']}L | "
                    f"Scored avg {analysis['home_form']['avg_for']:.2f} | "
                    f"Conceded avg {analysis['home_form']['avg_against']:.2f}"
                )
                st.write(
                    f"- Away: {analysis['away_form']['wins']}W / "
                    f"{analysis['away_form']['draws']}D / {analysis['away_form']['losses']}L | "
                    f"Scored avg {analysis['away_form']['avg_for']:.2f} | "
                    f"Conceded avg {analysis['away_form']['avg_against']:.2f}"
                )

                if analysis["home_pos"] and analysis["away_pos"]:
                    st.write(
                        f"**Standings:** Home #{analysis['home_pos']} ({analysis['home_pts']} pts) | "
                        f"Away #{analysis['away_pos']} ({analysis['away_pts']} pts)"
                    )

            st.markdown('</div>', unsafe_allow_html=True)

except requests.exceptions.HTTPError as e:
    st.error(f"HTTP error: {e}")
except requests.exceptions.RequestException as e:
    st.error(f"Request error: {e}")
except Exception as e:
    st.error(f"Unexpected error: {e}")
