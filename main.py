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
# =========================
# API FOOTBALL
# =========================

headers = {
    "x-rapidapi-key": os.environ["FOOTBALL_API_KEY"],
    "x-rapidapi-host": "api-football-v1.p.rapidapi.com"
}

# Bundesliga = league 78

today_url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures?league=78&season=2025&date={today_str}"

today_response = requests.get(today_url, headers=headers).json()

today_games = ""

for game in today_response["response"]:
    home = game["teams"]["home"]["name"]
    away = game["teams"]["away"]["name"]

    today_games += f"{home} vs {away}\n"

# =========================
# GESTERN
# =========================

yesterday_url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures?league=78&season=2025&date={yesterday_str}"

yesterday_response = requests.get(yesterday_url, headers=headers).json()

yesterday_games = ""

for game in yesterday_response["response"]:
    home = game["teams"]["home"]["name"]
    away = game["teams"]["away"]["name"]

    hs = game["goals"]["home"]
    aw = game["goals"]["away"]

    yesterday_games += f"{home} {hs}:{aw} {away}\n"
# =========================
# KI ZUSAMMENFASSUNG
# =========================
client = Groq(
    api_key=os.environ["GROQ_API_KEY"]
)

prompt = f"""
Fasse diese Fußballspiele kurz auf Deutsch zusammen.

Gestern:
{yesterday_games}

Heute:
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
