import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import json
import re
from fractions import Fraction
import unicodedata
API_KEY = st.secrets["odds_api_key"]

@st.cache_data(ttl=20)
def get_leaderboard():
    URL = "https://www.pgatour.com/leaderboard"
    r = requests.get(URL, verify=False)
    soup = BeautifulSoup(r.content, "html.parser")
    leader_json = json.loads(soup.find('script', {'id': 'leaderboard-seo-data'}).string)

    data = []
    for x in range(8):
        data.append([item['csvw:value'] for item in leader_json['mainEntity']['csvw:tableSchema']['csvw:columns'][x]['csvw:cells']])

    leaderboard = pd.DataFrame(data).transpose()
    leaderboard.columns = ['Position', 'Name', 'Current Score', 'Hole', 'Round 1', 'Round 2', 'Round 3', 'Round 4']

    def convert_to_float(value):
        if isinstance(value, str):
            try:
                if value == 'E':
                    return 0.0
                elif value in ('WD', 'DQ'):
                    return 100.0
                return float(value)
            except ValueError:
                return 0.0
        return float(value)

    leaderboard['CurrentScore'] = leaderboard['Current Score'].apply(convert_to_float)
    return leaderboard


def get_odds():
    url = "https://api.the-odds-api.com/v4/sports/golf_masters_tournament_winner/odds"
    params = {
        "apiKey": API_KEY,
        "regions": "us",
        "markets": "outrights",
        "oddsFormat": "decimal",
        "dateFormat": "iso"
    }

    r = requests.get(url, params=params)
    if r.status_code != 200:
        st.warning("Could not load odds data.")
        return {}

    odds_data = r.json()
    odds_map = {}

    for event in odds_data:
        for bookmaker in event.get("bookmakers", []):
            for market in bookmaker.get("markets", []):
                if market["key"] == "outrights":
                    for outcome in market["outcomes"]:
                        name = outcome["name"]
                        surname = normalize_name(name.split()[-1])
                        odds_map[surname] = outcome["price"]
    return odds_map


def decimal_to_fractional(decimal_odds):
    if pd.isna(decimal_odds):
        return None
    fractional = Fraction(decimal_odds).limit_denominator()
    return f"{fractional.numerator}/{fractional.denominator}"


def normalize_name(name):
    # Remove accents and convert to plain ASCII
    return unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('utf-8').lower()

# Your players dictionary (keep this global so it's reusable)
dictionary = {
        'Alex': ['S. Scheffler', 'W. Clark', 'T. Detry', 'K. Yu'],
        'Angus': ['T. Hatton', 'D. Johnson', 'L. Canter', 'C. Davis'],
        'Ben': ['H. Matsuyama', 'S. Burns', 'Cam. Young', 'A. Eckroat'],
        'Ed': ['J. Thomas', 'D. Thompson', 'M. Fitzpatrick', 'N. Dunlap'],
        'Fred W': ['W. Zalatoris', 'S. Im', 'A. Scott', 'C. Bezuidenhout'],
        'Freddie I': ['R. Henley', 'S. Garcia', 'S. Theegala', 'Z. Johnson'],
        'Henry': ['R. McIlroy', 'Ca. Smith', 'J.T. Poston', 'D. Willett'],
        'Jack': ['J. Niemann', 'M. Lee', 'T. Pendrith', 'M. Homa'],
        'Jam': ['R. MacIntyre', 'D. Berger', 'D. McCarthy', 'J. Vegas'],
        'Latham': ['P. Cantlay', 'J. Spaun', 'H. English', 'M. Pavon'],
        'Lom': ['J. Rahm', 'P. Reed', 'L. Glover', 'R. Højgaard'],
        'Macca': ['B. Koepka', 'T. Finau', 'N. Højgaard', 'N. Taylor'],
        'Mark': ['L. Åberg', 'J. Day', 'B. An', 'C. Kirk'],
        'Matt': ['S. Lowry', 'B. Harman', 'A. Rai', 'S. Jaeger'],
        'Max': ['T. Fleetwood', 'T. Kim', 'M. Kim', 'N. Echavarria'],
        'Mikey': ['V. Hovland', 'J. Rose', 'M. Greyserman', 'D. Riley'],
        'Sam': ['C. Morikawa', 'C. Conners', 'M. McNealy', 'T. Hoge'],
        'Sean': ['X. Schauffele', 'K. Bradley', 'B. Horschel', 'J. Highsmith'],
        'Seb': ['B. DeChambeau', 'S. Straka', 'P. Mickelson', 'B. Watson'],
        'Toby': ['J. Spieth', 'A. Bhatia', 'C. Schwartzel', 'M. McCarty']
    }

# ---------- Streamlit App ----------
st.set_page_config(page_title="Masters Leaderboard", layout="wide")
st.title("🏌️ Masters 2025 - Friends Leaderboard")

# Pull leaderboard data
leaderboard = get_leaderboard()

# === Main Leaderboard (Avg of Top 2) ===
rows = []
for person, picks in dictionary.items():
    scores = []
    for pick in picks:
        row = leaderboard[leaderboard['Name'] == pick]
        score = row.iloc[0]['CurrentScore'] if not row.empty else 100.0
        scores.append((pick, score))
    sorted_scores = sorted(scores, key=lambda x: x[1])
    avg_score = (sorted_scores[0][1] + sorted_scores[1][1]) / 2
    row_data = [person, avg_score]
    for player, score in sorted_scores:
        row_data.extend([player, score])
    rows.append(row_data)

columns = ['Person', 'Avg Score']
for i in range(1, 5):
    columns.extend([f'Player {i}', f'Score {i}'])

df_main = pd.DataFrame(rows, columns=columns).sort_values(by='Avg Score').reset_index(drop=True)
st.subheader("🏆 Leaderboard (Average of Top 2 Picks)")
st.dataframe(df_main, use_container_width=True)

rows = []
for person, picks in dictionary.items():
    for pick in picks:
        row = leaderboard[leaderboard['Name'] == pick]
        score = row.iloc[0]['CurrentScore'] if not row.empty else 100.0
        rows.append([person, pick, score])

df_outright = pd.DataFrame(rows, columns=["Person", "Player", "Score"])

# Get odds
odds_map = get_odds()

# Match by surname
df_outright["Surname"] = df_outright["Player"].apply(
    lambda x: normalize_name(re.sub(r"[^\w\s]", "", x.split()[-1]))
)
df_outright["Odds"] = df_outright["Surname"].map(odds_map)
df_outright["Fractional Odds"] = df_outright["Odds"].apply(decimal_to_fractional)


# Clean up
df_outright = df_outright.drop(columns=["Surname"])
df_outright = df_outright.sort_values(by="Score").reset_index(drop=True)

# Display
st.subheader("🎯 Outright Winner Tracker (with Betting Odds)")
st.dataframe(df_outright, use_container_width=True)
