import streamlit as st
import requests
from datetime import datetime

st.set_page_config(page_title="ستات رادار AI", page_icon="⚽", layout="wide")

API_TOKEN = st.secrets["FOOTBALL_DATA_API_KEY"]
BASE_URL = "https://api.football-data.org/v4"
HEADERS = {"X-Auth-Token": API_TOKEN}

st.markdown("""
<style>
.main {
    direction: rtl;
}
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
    font-size: 30px;
    font-weight: 800;
    margin-bottom: 8px;
}
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=300)
def api_get(endpoint, params=None):
    response = requests.get(
        f"{BASE_URL}{endpoint}",
        headers=HEADERS,
        params=params,
        timeout=20
    )
    response.raise_for_status()
    return response.json()

@st.cache_data(ttl=300)
def get_today_matches():
    data = api_get("/matches")
    return data.get("matches", [])

@st.cache_data(ttl=1800)
def get_team_finished_matches(team_id, limit=6):
    data = api_get(
        f"/teams/{team_id}/matches",
        params={"status": "FINISHED", "limit": limit}
    )
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
    except Exception:
        return utc_date

def extract_team_form(matches, team_id):
    played = 0
    wins = 0
    draws = 0
    losses = 0
    goals_for = 0
    goals_against = 0

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
        goals_pick = "أوفر 1.5 يبدو قويًا"
    elif total_goals_signal >= 1.8:
        goals_pick = "أوفر 1.5 ممكن"
    else:
        goals_pick = "أندر 3.5 يبدو أكثر أمانًا"

    home_name = home.get("name", "الفريق الأول")
    away_name = away.get("name", "الفريق الثاني")

    if home_prob > away_prob + 8:
        winner_pick = f"أفضلية نسبية لـ {home_name}"
    elif away_prob > home_prob + 8:
        winner_pick = f"أفضلية نسبية لـ {away_name}"
    else:
        winner_pick = "المباراة متوازنة نسبيًا"

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

def get_stat(match, keys):
    current = match
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key)
        else:
            return None
    return current

st.markdown('<div class="section-title">⚽ ستات رادار AI</div>', unsafe_allow_html=True)
st.caption("مباريات اليوم + تحليل مبني على بيانات حقيقية")

try:
    matches = get_today_matches()

    if not matches:
        st.warning("لا توجد مباريات اليوم.")
    else:
        st.success(f"تم الاتصال بالـ API بنجاح. عدد المباريات: {len(matches)}")

        for match in matches:
            home = match.get("homeTeam", {}).get("name", "غير معروف")
            away = match.get("awayTeam", {}).get("name", "غير معروف")
            competition = match.get("competition", {}).get("name", "بطولة غير معروفة")
            utc_date = format_time(match.get("utcDate", ""))
            status = match.get("status", "غير معروف")

            st.markdown('<div class="match-card">', unsafe_allow_html=True)
            st.markdown(f'<div class="team-line">{home} × {away}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="small-muted">البطولة: {competition}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="small-muted">التوقيت: {utc_date}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="small-muted">الحالة: {status}</div>', unsafe_allow_html=True)

            corners_home = get_stat(match, ["statistics", "corners", "home"])
            corners_away = get_stat(match, ["statistics", "corners", "away"])
            yellow_home = get_stat(match, ["statistics", "yellowCards", "home"])
            yellow_away = get_stat(match, ["statistics", "yellowCards", "away"])
            shots_home = get_stat(match, ["statistics", "shotsOnTarget", "home"])
            shots_away = get_stat(match, ["statistics", "shotsOnTarget", "away"])

            st.write("**إحصائيات المباراة:**")

            if corners_home is not None and corners_away is not None:
                st.write(f"- الركنيات: {home} {corners_home} | {away} {corners_away}")
            else:
                st.write("- الركنيات: غير متاحة في الخطة الحالية")

            if yellow_home is not None and yellow_away is not None:
                st.write(f"- البطاقات الصفراء: {home} {yellow_home} | {away} {yellow_away}")
            else:
                st.write("- البطاقات الصفراء: غير متاحة في الخطة الحالية")

            if shots_home is not None and shots_away is not None:
                st.write(f"- التسديدات على المرمى: {home} {shots_home} | {away} {shots_away}")
            else:
                st.write("- التسديدات على المرمى: غير متاحة في الخطة الحالية")

            if st.button("تحليل المباراة", key=f"analyze_{match.get('id')}"):
                analysis = analyze_match(match)

                st.info(f"درجة الثقة: {analysis['confidence']}%")
                st.write(f"**قراءة المباراة:** {analysis['winner_pick']}")
                st.write(f"**قراءة الأهداف:** {analysis['goals_pick']}")
                st.write(
                    f"**الاحتمالات:** فوز {home} {analysis['home_prob']}% | "
                    f"تعادل {analysis['draw_prob']}% | "
                    f"فوز {away} {analysis['away_prob']}%"
                )

                st.write("**فورمة آخر المباريات:**")

                st.write(
                    f"- {home}: {analysis['home_form']['wins']} فوز / "
                    f"{analysis['home_form']['draws']} تعادل / "
                    f"{analysis['home_form']['losses']} خسارة | "
                    f"معدل التسجيل {analysis['home_form']['avg_for']:.2f} | "
                    f"معدل استقبال الأهداف {analysis['home_form']['avg_against']:.2f}"
                )

                st.write(
                    f"- {away}: {analysis['away_form']['wins']} فوز / "
                    f"{analysis['away_form']['draws']} تعادل / "
                    f"{analysis['away_form']['losses']} خسارة | "
                    f"معدل التسجيل {analysis['away_form']['avg_for']:.2f} | "
                    f"معدل استقبال الأهداف {analysis['away_form']['avg_against']:.2f}"
                )

                if analysis["home_pos"] and analysis["away_pos"]:
                    st.write(
                        f"**الترتيب:** {home} #{analysis['home_pos']} ({analysis['home_pts']} نقطة) | "
                        f"{away} #{analysis['away_pos']} ({analysis['away_pts']} نقطة)"
                    )

            st.markdown('</div>', unsafe_allow_html=True)

except requests.exceptions.HTTPError as e:
    st.error(f"خطأ HTTP: {e}")
except requests.exceptions.RequestException as e:
    st.error(f"خطأ في الاتصال: {e}")
except Exception as e:
    st.error(f"خطأ غير متوقع: {e}")
