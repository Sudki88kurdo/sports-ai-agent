import requests
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from groq import Groq
import os

# =========================
# DATUM
# =========================

today = datetime.today()
yesterday = today - timedelta(days=1)

today_str = today.strftime("%Y-%m-%d")
yesterday_str = yesterday.strftime("%Y-%m-%d")

# =========================
# FOOTBALL DATA API
# =========================

headers = {
    "X-Auth-Token": os.environ["FOOTBALL_API_KEY"]
}

# Spiele holen
matches_url = "https://api.football-data.org/v4/matches"

matches_response = requests.get(
    matches_url,
    headers=headers
).json()

# Bundesliga Tabelle holen
standings_url = (
    "https://api.football-data.org/v4/competitions/BL1/standings"
)

standings_response = requests.get(
    standings_url,
    headers=headers
).json()

# Tabellenplätze speichern
team_positions = {}

table = standings_response["standings"][0]["table"]

for team in table:

    name = team["team"]["name"]
    position = team["position"]

    team_positions[name] = position

today_games = ""
yesterday_games = ""

# =========================
# SPIELE
# =========================

for match in matches_response.get("matches", []):

    utc_date = match["utcDate"][:10]

    home = match["homeTeam"]["name"]
    away = match["awayTeam"]["name"]

    status = match["status"]

    competition = match["competition"]["name"]

    matchday = match.get("matchday", "?")

    home_position = team_positions.get(home, "?")
    away_position = team_positions.get(away, "?")

    # =========================
    # HEUTE
    # =========================

    if utc_date == today_str:

        today_games += f"""
⚽ {home} vs {away}

🏆 Liga: {competition}
📅 Spieltag: {matchday}

📊 Tabellenplätze:
- {home}: Platz {home_position}
- {away}: Platz {away_position}

"""

    # =========================
    # GESTERN
    # =========================

    if utc_date == yesterday_str and status == "FINISHED":

        home_score = match["score"]["fullTime"]["home"]
        away_score = match["score"]["fullTime"]["away"]

        yesterday_games += f"""
✅ {home} {home_score}:{away_score} {away}

🏆 Liga: {competition}
📅 Spieltag: {matchday}

📊 Tabellenplätze:
- {home}: Platz {home_position}
- {away}: Platz {away_position}

"""

# Falls nichts gefunden
if today_games == "":
    today_games = "Keine Spiele gefunden.\n"

if yesterday_games == "":
    yesterday_games = "Keine Ergebnisse gefunden.\n"


# =========================
# EMAIL TEXT
# =========================

message = f"""
📅 HEUTE ({today_str})

{today_games}

📅 GESTERN ({yesterday_str})

{yesterday_games}
"""

# =========================
# KI ZUSAMMENFASSUNG
# =========================

client = Groq(
    api_key=os.environ["GROQ_API_KEY"]
)

ai_response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[
        {
            "role": "user",
            "content": f"""
            Analysiere diese Fußballspiele auf Deutsch.
            
            Für jedes Spiel schreibe:
            
            - welche Teams spielen
            - in welchem Stadion gespielt wird
            - welcher Spieltag oder welche Runde das ist
            - das Ergebnis falls vorhanden
            - die aktuelle Platzierung der Teams in der Liga
            
            Schreibe alles übersichtlich und gut lesbar.
            
            Beispiel:
            
            ⚽ Dortmund vs Bayern
            🏟 Stadion: Signal Iduna Park
            📅 Spieltag: 32
            📊 Tabellenplätze:
            - Dortmund: Platz 4
            - Bayern: Platz 1
            
            Hier sind die Spieldaten:
            
            {message}
            """        }
    ]
)

summary = ai_response.choices[0].message.content

final_message = "\n\n🧠 KI ZUSAMMENFASSUNG:\n\n" + summary

# =========================
# EMAIL SENDEN
# =========================

sender = os.environ["EMAIL_USER"]
password = os.environ["EMAIL_PASS"]

msg = MIMEText(final_message)

msg["Subject"] = "⚽ Fußball Update"
msg["From"] = sender
msg["To"] = sender

server = smtplib.SMTP_SSL("smtp.gmail.com", 465)

server.login(sender, password)
server.send_message(msg)

server.quit()

print("Email gesendet!")
