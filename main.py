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
# HEUTIGE SPIELE
# =========================

# Bundesliga = league 78

# =========================
# API FOOTBALL
# =========================

headers = {
    "x-rapidapi-key": os.environ["FOOTBALL_API_KEY"],
    "x-rapidapi-host": "api-football-v1.p.rapidapi.com"
}

current_season = datetime.today().year

# Mehrere wichtige Ligen
leagues = [78, 39, 140, 2]

today_games = ""
yesterday_games = ""

# =========================
# HEUTE
# =========================

for league in leagues:

    today_url = (
        f"https://api-football-v1.p.rapidapi.com/v3/fixtures"
        f"?league={league}&season={current_season}&date={today_str}"
    )

    response = requests.get(today_url, headers=headers).json()

    for game in response.get("response", []):
        home = game["teams"]["home"]["name"]
        away = game["teams"]["away"]["name"]

        today_games += f"{home} vs {away}\n"

# =========================
# GESTERN
# =========================

for league in leagues:

    yesterday_url = (
        f"https://api-football-v1.p.rapidapi.com/v3/fixtures"
        f"?league={league}&season={current_season}&date={yesterday_str}"
    )

    response = requests.get(yesterday_url, headers=headers).json()

    for game in response.get("response", []):
        home = game["teams"]["home"]["name"]
        away = game["teams"]["away"]["name"]

        hs = game["goals"]["home"]
        aw = game["goals"]["away"]

        yesterday_games += f"{home} {hs}:{aw} {away}\n"

# Falls nichts gefunden
if today_games == "":
    today_games = "Keine Spiele gefunden."

if yesterday_games == "":
    yesterday_games = "Keine Ergebnisse gefunden."
    
# =========================
# KI ZUSAMMENFASSUNG
# =========================
client = Groq(
    api_key=os.environ["GROQ_API_KEY"]
)

prompt = f"""
Fasse diese Fußballspiele kurz auf Deutsch zusammen.

Gestern, Datum:
{yesterday_games}

Heute, Datum:
{today_games}
"""

response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[
        {
            "role": "user",
            "content": prompt
        }
    ]
)

summary = response.choices[0].message.content

# =========================
# EMAIL SENDEN
# =========================
sender = os.environ["EMAIL_USER"]
password = os.environ["EMAIL_PASS"]
receiver = os.environ["EMAIL_USER"]

msg = MIMEText(summary)

msg["Subject"] = "⚽ Fußball Update"
msg["From"] = sender
msg["To"] = receiver

server = smtplib.SMTP_SSL("smtp.gmail.com", 465)

server.login(sender, password)
server.send_message(msg)
server.quit()

print("Email gesendet!")
