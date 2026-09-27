import os, json, time, requests
import yfinance as yf
import pandas as pd

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT = os.getenv("CHAT_ID")
SYM = "GC=F"
FILE = "state.json"

def send(msg):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        data = {"chat_id": CHAT, "text": msg, "parse_mode": "Markdown"}
        requests.post(url, data=data, timeout=10)
    except Exception as e:
        print(e)

def load_state():
    try:
        with open(FILE, "r") as f:
            return json.load(f)
    except:
        return {"active": None}

def save_state(d):
    with open(FILE, "w") as f:
        json.dump(d, f)

def calc_vidya(close, period=14):
    diff = close.diff()
    up = diff.clip(lower=0).rolling(period).sum()
    down = diff.abs().rolling(period).sum()
    cmo = 100 * (up / down.replace(0, 1))
    k = cmo / 100
    vidya = []
    v = 0
    for i in range(len(close)):
        if i == 0:
            v = close.iloc[i]
        else:
            v = float(k.iloc[i]) * float(close.iloc[i]) + (1 - float(k.iloc[i])) * v
        vidya.append(v)
    return pd.Series(vidya, index=close.index)

def get_data(tf):
    df = yf.download(SYM, period="5d", interval=tf, progress=False, auto_adjust=True)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df["VIDYA"] = calc_vidya(df["Close"])
    return df

send("✅ BOT 2 SMC VIDYA LIVE - 1H+15M+5M | BOS + DSL")

while True:
    try:
        state = load_state()
        d1h = get_data("1h")
        d15 = get_data("15m")
        d5 = get_data("5m")

        price = float(d5["Close"].iloc[-1])
        v1h = float(d1h["VIDYA"].iloc[-1])
        v15 = float(d15["VIDYA"].iloc[-1])
        v5 = float(d5["VIDYA"].iloc[-1])
        high = float(d5["High"].iloc[-1])
        low = float(d5["Low"].iloc[-1])

        active = state.get("active")

        if active:
            entry = active["entry"]
            sl = active["sl"]
            tp1 = active["tp1"]
            tp2 = active["tp2"]
            side = active["side"]

            if side == "LONG":
                if low <= sl:
                    state["active"] = None
                    save_state(state)
                    send(f"❌ SL HIT LONG Entry {entry}")
                elif high >= tp1 and not active.get("tp1_hit"):
                    active["tp1_hit"] = True
                    state["active"] = active
                    save_state(state)
                    send(f"💰 TP1 HIT LONG Entry {entry} Now {price}")
                elif high >= tp2:
                    state["active"] = None
                    save_state(state)
                    send(f"💰💰 TP2 HIT LONG Entry {entry}")

            if side == "SHORT":
                if high >= sl:
                    state["active"] = None
                    save_state(state)
                    send(f"❌ SL HIT SHORT Entry {entry}")
                elif low <= tp1 and not active.get("tp1_hit"):
                    active["tp1_hit"] = True
                    state["active"] = active
                    save_state(state)
                    send(f"💰 TP1 HIT SHORT Entry {entry} Now {price}")
                elif low <= tp2:
                    state["active"] = None
                    save_state(state)
                    send(f"💰💰 TP2 HIT SHORT Entry {entry}")

        else:
            above = price > v1h and price > v15 and price > v5
            below = price < v1h and price < v15 and price < v5
            bos_up = d5["Close"].iloc[-1] > d5["High"].iloc[-2]
            bos_down = d5["Close"].iloc[-1] < d5["Low"].iloc[-2]

            if below and bos_down:
                entry = round(price, 2)
                sl = round(price + 3, 2)
                tp1 = round(price - 5, 2)
                tp2 = round(price - 10, 2)
                state["active"] = {"side": "SHORT", "entry": entry, "sl": sl, "tp1": tp1, "tp2": tp2, "tp1_hit": False}
                save_state(state)
                send(f"🔴 SHORT VALID Entry {entry} SL {sl} TP1 {tp1} TP2 {tp2}")

            if above and bos_up:
                entry = round(price, 2)
                sl = round(price - 3, 2)
                tp1 = round(price + 5, 2)
                tp2 = round(price + 10, 2)
                state["active"] = {"side": "LONG", "entry": entry, "sl": sl, "tp1": tp1, "tp2": tp2, "tp1_hit": False}
                save_state(state)
                send(f"🟢 LONG SCALP Entry {entry} SL {sl} TP1 {tp1} TP2 {tp2}")

        time.sleep(300)

    except Exception as e:
        print(f"Error {e}")
        time.sleep(60)
