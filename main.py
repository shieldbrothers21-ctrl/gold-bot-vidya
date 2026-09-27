import time
import requests
import os
from datetime import datetime

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID") or os.getenv("TELEGRAM_CHAT_ID")

def send_telegram(msg):
    if not TOKEN or not CHAT_ID:
        print("Missing TOKEN or CHAT_ID")
        return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)
        print(f"Telegram sent: {msg[:50]}")
    except Exception as e:
        print(f"Telegram error: {e}")

# SEND LIVE MESSAGE IMMEDIATELY - BEFORE YAHOO!
send_telegram("✅ *BOT 2 SMC VIDYA LIVE - 1H+15M+5M | BOS + DSL*\n\nBot started at " + datetime.now().strftime("%H:%M:%S") + " - Waiting for XAU signal...")

# Now import yfinance AFTER telegram
import yfinance as yf

def get_gold_price():
    try:
        # Add headers to avoid 429
        ticker = yf.Ticker("GC=F")
        data = ticker.history(period="1d", interval="5m")
        if not data.empty:
            return float(data['Close'].iloc[-1])
    except Exception as e:
        print(f"Gold fetch error: {e}")
    return None

print("Bot running... checking every 5 minutes")
while True:
    price = get_gold_price()
    if price:
        print(f"Gold: {price}")
    else:
        print("Retrying in 60s - Yahoo rate limited, will retry...")
        time.sleep(60)
        continue
    time.sleep(300)
