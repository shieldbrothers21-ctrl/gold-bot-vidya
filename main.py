import os, time, threading, requests
from flask import Flask
from datetime import datetime

BOT_TOKEN = "8605505295:AAFkhFLSaULiQ-tEvVbyFvUw2SHuJ5J6nC8"
CHAT_ID = "8313326862"

# --- GOLD ONANA API (Real XAU Spot) ---
GOLD_ONANA_API = "https://api.gold-api.com/price/XAU"

app = Flask(__name__)
@app.route('/')
def home():
    return "BOT 2 SMC VIDYA LIVE - GOLD ONANA REAL SPOT - 1H+15M+5M | BOS + DSL - 24/7!"

def send_tg(msg):
    try:
        requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", params={"chat_id": CHAT_ID, "text": msg}, timeout=10)
    except: pass

def get_gold_onana():
    try:
        # GOLD ONANA real price
        r = requests.get(GOLD_ONANA_API, timeout=10).json()
        price = float(r['price'])
        print(f"GOLD ONANA: {price}")
        return price
    except:
        return None

prices_5m = []
prices_15m = []
prices_1h = []

def bot_loop():
    global prices_5m, prices_15m, prices_1h
    send_tg(f"✅ BOT 2 SMC VIDYA LIVE - GOLD ONANA\nStarted {datetime.now().strftime('%H:%M:%S')} - Using GOLD ONANA Real Spot")
    print("BOT 2 GOLD ONANA STARTING...")
    c = 0
    while True:
        try:
            xau = get_gold_onana()
            if not xau: 
                time.sleep(10)
                continue
            c += 1
            prices_5m.append(xau)
            if c % 3 == 0: prices_15m.append(xau)
            if c % 12 == 0: prices_1h.append(xau)
            prices_5m = prices_5m[-100:]
            prices_15m = prices_15m[-100:]
            prices_1h = prices_1h[-100:]
            print(f"GOLD ONANA {xau:.2f} | 5M {len(prices_5m)} | 15M {len(prices_15m)} | 1H {len(prices_1h)}")
            sig = None
            if len(prices_5m) >= 50:
                rh = max(prices_5m[-20:-1])
                rl = min(prices_5m[-20:-1])
                ef = sum(prices_5m[-10:]) / 10
                es = sum(prices_5m[-50:]) / 50
                if xau > rh and ef > es:
                    sl = rl
                    sig = f"🚀 GOLD ONANA BULLISH BOS + VIDYA\nBreak {rh:.2f}->{xau:.2f}\n\n✅ ENTRY: {xau:.2f} GOLD ONANA SPOT\n🛑 SL: {sl:.2f}\n🎯 TP1: {xau+(xau-sl):.2f}\n🎯 TP2: {xau+(xau-sl)*2:.2f}"
                elif xau < rl and ef < es:
                    sl = rh
                    sig = f"🔥 GOLD ONANA BEARISH BOS + VIDYA\nBreak {rl:.2f}->{xau:.2f}\n\n❌ ENTRY: {xau:.2f} GOLD ONANA SPOT\n🛑 SL: {sl:.2f}\n🎯 TP1: {xau-(sl-xau):.2f}\n🎯 TP2: {xau-(sl-xau)*2:.2f}"
            if sig:
                send_tg(sig)
                time.sleep(300)
            time.sleep(10)
        except Exception as e:
            print(e)
            time.sleep(10)

threading.Thread(target=bot_loop, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
