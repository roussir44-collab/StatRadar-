import streamlit as st
import requests
import streamlit.components.v1 as components
from datetime import datetime

st.set_page_config(page_title="StatRadar AI", page_icon="⚽", layout="wide")

API_TOKEN = st.secrets["FOOTBALL_DATA_API_KEY"]
BASE_URL = "https://api.football-data.org/v4"
HEADERS = {"X-Auth-Token": API_TOKEN}

PROMO_CODE = "GA3NERBHOU"
MAIN_AFFILIATE_LINK = "https://refpa3665.com/L?tag=d_5731021m_59351c_&site=5731021&ad=59351"

st.markdown("""
<style>
html, body, [class*="css"] {
    direction: rtl;
}
.block-container {
    padding-top: 1.5rem;
    padding-bottom: 2rem;
    max-width: 1200px;
}
.hero {
    background: linear-gradient(135deg, #111827, #0f172a);
    padding: 28px;
    border-radius: 22px;
    color: white;
    margin-bottom: 18px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.18);
}
.hero-title {
    font-size: 34px;
    font-weight: 800;
    margin-bottom: 8px;
}
.hero-sub {
    color: #d1d5db;
    font-size: 15px;
    line-height: 1.8;
}
.offer-box {
    background: linear-gradient(135deg, #fbbf24, #f59e0b);
    color: #111827;
    border-radius: 20px;
    padding: 22px;
    margin: 18px 0 20px 0;
    box-shadow: 0 10px 25px rgba(245, 158, 11, 0.25);
}
.offer-title {
    font-size: 28px;
    font-weight: 800;
    margin-bottom: 6px;
}
.offer-sub {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 14px;
}
.offer-code {
    background: rgba(255,255,255,0.75);
    padding: 14px 18px;
    border-radius: 14px;
    font-size: 24px;
    font-weight: 800;
    text-align: center;
    letter-spacing: 1px;
    margin-bottom: 14px;
}
.match-card {
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 18px;
    padding: 18px;
    margin-bottom: 16px;
    box-shadow: 0 6px 18px rgba(0,0,0,0.05);
}
.match-title {
    font-size: 24px;
    font-weight: 800;
    margin-bottom: 10px;
    color: #111827;
}
.meta {
    color: #6b7280;
    font-size: 14px;
    margin-bottom: 4px;
}
.badge {
    display: inline-block;
    padding: 6px 12px;
    background: #eef2ff;
    color: #3730a3;
    border-radius: 999px;
    font-size: 13px;
    font-weight: 600;
    margin-top: 8px;
}
.box {
    background: #f8fafc;
    border: 1px solid #e5e7eb;
    border-radius: 14px;
    padding: 14px;
    margin-bottom: 10px;
}
.box-title {
    font-weight: 700;
    margin-bottom: 6px;
    color: #111827;
}
.mini-offer {
    background: #fff7ed;
    border: 1px solid #fdba74;
    border-radius: 16px;
    padding: 16px;
    margin-top: 12px;
}
.mini-offer-title {
    font-weight: 800;
    font-size: 18px;
    margin-bottom: 6px;
    color: #9a3412;
}
.copy-btn-wrap {
    margin-top: 8px;
    margin-bottom: 8px;
}
.copy-button {
    background: #111827;
    color: white;
    border: none;
    border-radius: 12px;
    padding: 10px 16px;
    font-size: 14px;
    font-weight: 700;
    cursor: pointer;
    width: 100%;
}
.disclosure {
    font-size: 12px;
    color: #4b5563;
    margin-top: 10px;
    line-height: 1.7;
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
        "avg_for": avg_for,
        "avg_against": avg_against,
        "form_points": form_points
    }

def calc_goal_markets(matches, team_id):
    played = 0
    over_15 = 0
    over_25 = 0
    btts_yes = 0

    for m in matches:
        home_id = m.get("homeTeam", {}).get("id")
        away_id = m.get("awayTeam", {}).get("id")
        full = m.get("score", {}).get("fullTime", {})
        hg = full.get("home")
        ag = full.get("away")

        if hg is None or ag is None:
            continue

        if home_id != team_id and away_id != team_id:
            continue

        total_goals = hg + ag
        both_scored = hg > 0 and ag > 0

        played += 1

        if total_goals >= 2:
            over_15 += 1
        if total_goals >= 3:
            over_25 += 1
        if both_scored:
            btts_yes += 1

    if played == 0:
        return {
            "played": 0,
            "over15_rate": 0,
            "over25_rate": 0,
            "btts_rate": 0
        }

    return {
        "played": played,
        "over15_rate": round((over_15 / played) * 100),
        "over25_rate": round((over_25 / played) * 100),
        "btts_rate": round((btts_yes / played) * 100)
    }

def pick_confidence_label(value):
    if value >= 75:
        return "عالية"
    elif value >= 60:
        return "متوسطة"
    else:
        return "ضعيفة"

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

    home_markets = calc_goal_markets(home_matches, home_id)
    away_markets = calc_goal_markets(away_matches, away_id)

    home_pos, home_pts, home_gd = get_position(standings, home_id)
    away_pos, away_pts, away_gd = get_position(standings, away_id)

    home_strength = (
        home_form["form_points"] * 1.8 +
        home_form["avg_for"] * 2.2 -
        home_form["avg_against"] * 1.3 +
        1.2
    )

    away_strength = (
        away_form["form_points"] * 1.8 +
        away_form["avg_for"] * 2.2 -
        away_form["avg_against"] * 1.3
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

    over15_score = round((home_markets["over15_rate"] + away_markets["over15_rate"]) / 2)
    over25_score = round((home_markets["over25_rate"] + away_markets["over25_rate"]) / 2)
    btts_score = round((home_markets["btts_rate"] + away_markets["btts_rate"]) / 2)

    predictions = [
        {
            "title": "أكثر من 1.5 هدف",
            "score": over15_score,
            "confidence": pick_confidence_label(over15_score),
            "reason": f"آخر مباريات {home.get('name')} و{away.get('name')} تُظهر معدلًا جيدًا لبلوغ هدفين أو أكثر."
        },
        {
            "title": "أكثر من 2.5 هدف",
            "score": over25_score,
            "confidence": pick_confidence_label(over25_score),
            "reason": "هناك مؤشرات على مباراة مفتوحة نسبيًا إذا استمر نفس نسق الأهداف الأخير."
        },
        {
            "title": "تسجيل كلا الفريقين",
            "score": btts_score,
            "confidence": pick_confidence_label(btts_score),
            "reason": "الفريقان أظهرا قابلية للتسجيل واستقبال الأهداف في آخر المباريات."
        }
    ]

    predictions = sorted(predictions, key=lambda x: x["score"], reverse=True)

    home_name = home.get("name", "الفريق الأول")
    away_name = away.get("name", "الفريق الثاني")

    if home_prob > away_prob + 8:
        winner_pick = f"الأفضلية تميل إلى {home_name}"
    elif away_prob > home_prob + 8:
        winner_pick = f"الأفضلية تميل إلى {away_name}"
    else:
        winner_pick = "المواجهة متقاربة"

    confidence = min(88, max(55, abs(home_prob - away_prob) + 52))

    return {
        "winner_pick": winner_pick,
        "home_prob": home_prob,
        "draw_prob": draw_prob,
        "away_prob": away_prob,
        "confidence": confidence,
        "home_form": home_form,
        "away_form": away_form,
        "home_pos": home_pos,
        "away_pos": away_pos,
        "home_pts": home_pts,
        "away_pts": away_pts,
        "predictions": predictions
    }

def get_stat(match, keys):
    current = match
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key)
        else:
            return None
    return current

def copy_button_component(text_to_copy, button_text="نسخ الكود"):
    safe_text = text_to_copy.replace("'", "\\'")
    components.html(
        f"""
        <div class="copy-btn-wrap">
            <button class="copy-button" onclick="navigator.clipboard.writeText('{safe_text}')">
                {button_text}
            </button>
        </div>
        """,
        height=55,
    )

st.markdown("""
<div class="hero">
    <div class="hero-title">⚽ StatRadar AI</div>
    <div class="hero-sub">
        تابع مباريات اليوم، واكتشف التوصية الأقوى، وتوصيات إضافية مبنية على بيانات المباريات السابقة بشكل أوضح وأسهل.
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="offer-box">
    <div class="offer-title">استفد من العرض</div>
    <div class="offer-sub">مكافأة التسجيل</div>
    <div class="offer-code">{PROMO_CODE}</div>
    <div style="font-size:15px;font-weight:600;">انسخ الكود وسجّل من الرابط للاستفادة من العرض.</div>
</div>
""", unsafe_allow_html=True)

col_offer1, col_offer2 = st.columns(2)
with col_offer1:
    st.link_button("فتح العرض", MAIN_AFFILIATE_LINK, use_container_width=True)
with col_offer2:
    copy_button_component(PROMO_CODE, "نسخ البرومو كود")

st.markdown("""
<div class="disclosure">
هذا الموقع يحتوي على روابط أفلييت. +18 فقط. العب بمسؤولية.
</div>
""", unsafe_allow_html=True)

st.markdown("---")

try:
    matches = get_today_matches()

    if not matches:
        st.warning("لا توجد مباريات متاحة اليوم.")
    else:
        st.info(f"عدد المباريات المتاحة اليوم: {len(matches)}")

        for match in matches:
            home = match.get("homeTeam", {}).get("name", "غير معروف")
            away = match.get("awayTeam", {}).get("name", "غير معروف")
            competition = match.get("competition", {}).get("name", "بطولة غير معروفة")
            utc_date = format_time(match.get("utcDate", ""))
            status = match.get("status", "غير معروف")

            st.markdown('<div class="match-card">', unsafe_allow_html=True)
            st.markdown(f'<div class="match-title">{home} × {away}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="meta">البطولة: {competition}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="meta">التوقيت: {utc_date}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="badge">الحالة: {status}</div>', unsafe_allow_html=True)

            if st.button("تحليل المباراة", key=f"analyze_{match.get('id')}"):
                analysis = analyze_match(match)
                top_pick = analysis["predictions"][0]
                second_pick = analysis["predictions"][1]
                third_pick = analysis["predictions"][2]

                tab1, tab2, tab3 = st.tabs(["الخلاصة", "أداء آخر المباريات", "إحصائيات المباراة"])

                with tab1:
                    c1, c2, c3 = st.columns(3)
                    c1.metric(f"{home}", f"{analysis['home_prob']}%")
                    c2.metric("تعادل", f"{analysis['draw_prob']}%")
                    c3.metric(f"{away}", f"{analysis['away_prob']}%")

                    st.markdown(
                        f'<div class="box"><div class="box-title">قراءة المباراة</div>{analysis["winner_pick"]}</div>',
                        unsafe_allow_html=True
                    )

                    st.markdown(
                        f'<div class="box"><div class="box-title">التوصية الأقوى</div>'
                        f'{top_pick["title"]} — مستوى الثقة: {top_pick["confidence"]} ({top_pick["score"]}%)<br>'
                        f'{top_pick["reason"]}'
                        f'</div>',
                        unsafe_allow_html=True
                    )

                    st.markdown(
                        f'<div class="box"><div class="box-title">توصيات إضافية</div>'
                        f'1) {second_pick["title"]} — {second_pick["confidence"]} ({second_pick["score"]}%)<br>'
                        f'2) {third_pick["title"]} — {third_pick["confidence"]} ({third_pick["score"]}%)'
                        f'</div>',
                        unsafe_allow_html=True
                    )

                    st.markdown(
                        f'<div class="box"><div class="box-title">مستوى الثقة العام</div>{analysis["confidence"]}%</div>',
                        unsafe_allow_html=True
                    )

                    if analysis["home_pos"] and analysis["away_pos"]:
                        st.markdown(
                            f'<div class="box"><div class="box-title">الترتيب الحالي</div>'
                            f'{home}: المركز {analysis["home_pos"]} - {analysis["home_pts"]} نقطة<br>'
                            f'{away}: المركز {analysis["away_pos"]} - {analysis["away_pts"]} نقطة'
                            f'</div>',
                            unsafe_allow_html=True
                        )

                    st.markdown(
                        f'''
                        <div class="mini-offer">
                            <div class="mini-offer-title">استفد من العرض</div>
                            <div style="font-weight:700;margin-bottom:8px;">مكافأة التسجيل</div>
                            <div style="background:#fff;padding:10px 12px;border-radius:10px;font-weight:800;text-align:center;">
                                {PROMO_CODE}
                            </div>
                            <div style="font-size:14px;margin-top:8px;">
                                انسخ الكود وسجّل من الرابط للاستفادة من العرض.
                            </div>
                        </div>
                        ''',
                        unsafe_allow_html=True
                    )

                    mini1, mini2 = st.columns(2)
                    with mini1:
                        st.link_button("فتح العرض الآن", MAIN_AFFILIATE_LINK, use_container_width=True)
                    with mini2:
                        copy_button_component(PROMO_CODE, "نسخ الكود")

                with tab2:
                    st.markdown(
                        f'<div class="box"><div class="box-title">{home}</div>'
                        f'فوز: {analysis["home_form"]["wins"]} | '
                        f'تعادل: {analysis["home_form"]["draws"]} | '
                        f'خسارة: {analysis["home_form"]["losses"]}<br>'
                        f'معدل التسجيل: {analysis["home_form"]["avg_for"]:.2f}<br>'
                        f'معدل استقبال الأهداف: {analysis["home_form"]["avg_against"]:.2f}'
                        f'</div>',
                        unsafe_allow_html=True
                    )

                    st.markdown(
                        f'<div class="box"><div class="box-title">{away}</div>'
                        f'فوز: {analysis["away_form"]["wins"]} | '
                        f'تعادل: {analysis["away_form"]["draws"]} | '
                        f'خسارة: {analysis["away_form"]["losses"]}<br>'
                        f'معدل التسجيل: {analysis["away_form"]["avg_for"]:.2f}<br>'
                        f'معدل استقبال الأهداف: {analysis["away_form"]["avg_against"]:.2f}'
                        f'</div>',
                        unsafe_allow_html=True
                    )

                with tab3:
                    corners_home = get_stat(match, ["statistics", "corners", "home"])
                    corners_away = get_stat(match, ["statistics", "corners", "away"])
                    yellow_home = get_stat(match, ["statistics", "yellowCards", "home"])
                    yellow_away = get_stat(match, ["statistics", "yellowCards", "away"])
                    shots_home = get_stat(match, ["statistics", "shotsOnTarget", "home"])
                    shots_away = get_stat(match, ["statistics", "shotsOnTarget", "away"])

                    if corners_home is not None and corners_away is not None:
                        st.markdown(
                            f'<div class="box"><div class="box-title">الركنيات</div>{home}: {corners_home} | {away}: {corners_away}</div>',
                            unsafe_allow_html=True
                        )
                    else:
                        st.markdown(
                            '<div class="box"><div class="box-title">الركنيات</div>غير متاحة حاليًا</div>',
                            unsafe_allow_html=True
                        )

                    if yellow_home is not None and yellow_away is not None:
                        st.markdown(
                            f'<div class="box"><div class="box-title">البطاقات الصفراء</div>{home}: {yellow_home} | {away}: {yellow_away}</div>',
                            unsafe_allow_html=True
                        )
                    else:
                        st.markdown(
                            '<div class="box"><div class="box-title">البطاقات الصفراء</div>غير متاحة حاليًا</div>',
                            unsafe_allow_html=True
                        )

                    if shots_home is not None and shots_away is not None:
                        st.markdown(
                            f'<div class="box"><div class="box-title">التسديدات على المرمى</div>{home}: {shots_home} | {away}: {shots_away}</div>',
                            unsafe_allow_html=True
                        )
                    else:
                        st.markdown(
                            '<div class="box"><div class="box-title">التسديدات على المرمى</div>غير متاحة حاليًا</div>',
                            unsafe_allow_html=True
                        )

            st.markdown('</div>', unsafe_allow_html=True)

except requests.exceptions.HTTPError as e:
    st.error(f"خطأ HTTP: {e}")
except requests.exceptions.RequestException as e:
    st.error(f"خطأ في الاتصال: {e}")
except Exception as e:
    st.error(f"خطأ غير متوقع: {e}")
