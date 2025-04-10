import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import json


@st.cache_data(ttl=20)  # Caches data for 60 seconds to auto-refresh
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

    rows = []
    for person, picks in dictionary.items():
        scores = []
        for pick in picks:
            row = leaderboard[leaderboard['Name'] == pick]
            if not row.empty:
                score = row.iloc[0]['CurrentScore']
            else:
                score = 100.0
            scores.append((pick, score))

        scores_sorted = sorted(scores, key=lambda x: x[1])
        avg_score = (scores_sorted[0][1] + scores_sorted[1][1]) / 2

        row_data = [person, avg_score]
        for player, score in scores_sorted:
            row_data.extend([player, score])

        rows.append(row_data)

    columns = ['Person', 'Avg Score']
    for i in range(1, 5):
        columns.extend([f'Player {i}', f'Score {i}'])

    df_result = pd.DataFrame(rows, columns=columns)
    df_result = df_result.sort_values(by='Avg Score').reset_index(drop=True)

    return df_result


# ----------------------------
# Streamlit UI
# ----------------------------
st.set_page_config(page_title="Masters 2025 Leaderboard", layout="wide")

st.title("🏌️ Masters 2025 - Friends Leaderboard")
st.markdown("Updates every 60 seconds (may need to refresh page)")

df = get_leaderboard()
st.dataframe(df, use_container_width=True, height=600)
