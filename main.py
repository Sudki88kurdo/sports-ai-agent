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
today_url = f"https://www.thesportsdb.com/api/v1/json/3/eventsday.php?d={today_str}&s=Soccer"

today_data = requests.get(today_url).json()

today_games = ""

if today_data["events"]:
    for game in today_data["events"][:10]:
        today_games += f"{game['strHomeTeam']} vs {game['strAwayTeam']}\n"

# =========================
# GESTRIGE SPIELE
# =========================
yesterday_url = f"https://www.thesportsdb.com/api/v1/json/3/eventsday.php?d={yesterday_str}&s=Soccer"

yesterday_data = requests.get(yesterday_url).json()

yesterday_games = ""

if yesterday_data["events"]:
    for game in yesterday_data["events"][:10]:
        home = game['strHomeTeam']
        away = game['strAwayTeam']

        hs = game.get('intHomeScore')
        aw = game.get('intAwayScore')

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
    model="llama3-70b-8192",
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
