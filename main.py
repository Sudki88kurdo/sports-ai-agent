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

url = "https://api.football-data.org/v4/matches?status=FINISHED,SCHEDULED"

response = requests.get(url, headers=headers).json()

today_games = ""
yesterday_games = ""

# =========================
# SPIELE SORTIEREN
# =========================

for match in response.get("matches", []):

    utc_date = match["utcDate"][:10]

    home = match["homeTeam"]["name"]
    away = match["awayTeam"]["name"]

    status = match["status"]

    # =========================
    # HEUTE
    # =========================

    if utc_date == today_str:

        today_games += f"⚽ {home} vs {away}\n"

    # =========================
    # GESTERN
    # =========================

    if utc_date == yesterday_str and status == "FINISHED":

        home_score = match["score"]["fullTime"]["home"]
        away_score = match["score"]["fullTime"]["away"]

        yesterday_games += (
            f"✅ {home} {home_score}:{away_score} {away}\n"
        )
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
            "content": f"
            Fasse diese Fußballspiele kurz wo die statt findet,
            welche runde ist das im Liga, 
            und am Ende sag in welche Liga würde dieses Team platziert sein auf Deutsch zusammen:\n{message}"
        }
    ]
)

summary = ai_response.choices[0].message.content

final_message = message + "\n\n🧠 KI ZUSAMMENFASSUNG:\n\n" + summary

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
