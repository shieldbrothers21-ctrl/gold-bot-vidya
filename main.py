import os, time, requests
from datetime import datetime

def get_env_any(*names):
    all_env = {k.lower(): v for k,v in os.environ.items()}
    for n in names:
        if n.lower() in all_env:
            return all_env[n.lower()]
    return None

TOKEN = get_env_any("TOKEN","TELEGRAM_TOKEN","TELEGRAM_BOT_TOKEN","TELEGRAM","BOT_TOKEN","TELEGRA")
CHAT_ID = get_env_any("CHAT_ID","TELEGRAM_CHAT_ID")

print("TOKEN ok:", bool(TOKEN), "CHAT ok:", bool(CHAT_ID))

def send(msg):
    try:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": msg}, timeout=15)
        print("TG sent")
    except Exception as e:
        print(e)

def get_candles():
    url = "https://data-api.binance.vision/api/v3/klines?symbol=PAXGUSDT&interval=5m&limit=100"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        print("Binance status", r.status_code)
        data = r.json()
        candles = []
        for d in data:
            candles.append({"open": float(d[1]), "high": float(d[2]), "low": float(d[3]), "close": float(d[4])})
        print("Got candles", len(candles), "price", candles[-1]["close"])
        return candles
    except Exception as e:
        print("PAXG fail", e)
        return None

def calc_vidya(closes, period=20):
    v=[]
    for i in range(len(closes)):
        if i < period:
            v.append(closes[i])
            continue
        up = 0
        for k in range(i-period+1, i+1):
            if closes[k] > closes[k-1]:
                up += 1
        down = period - up
        ch = abs(up-down) / (up+down) if up+down else 0
        alpha = 0.2 * ch
        v.append(closes[i]*alpha + v[-1]*(1-alpha))
    return v

last_buy = 0
last_sell = 0

def check(closes, highs, lows, vidya):
    global last_buy, last_sell
    curr = closes[-1]
    prev = closes[-2]
    curr_v = vidya[-1]
    prev_v = vidya[-2]
    lh = max(highs[-6:-1])
    ll = min(lows[-6:-1])
    slw = min(lows[-5:])
    shw = max(highs[-5:])
    nh = max(highs[-20:]) + 1.5
    nl = min(lows[-20:]) - 1.5
    now = time.time()

    if prev < prev_v and curr > curr_v and curr > lh and now - last_buy > 1800:
        entry = curr + 0.6
        sl = slw - 0.5
        if entry - sl > 10:
            sl = entry - 9.5
        tp1 = entry + 6
        tp2 = entry + 11
        send("BULLISH VIDYA BOUNCE + BOS\nENTRY " + str(round(entry,2)) + " SL " + str(round(sl,2)) + " TP1 " + str(round(tp1,2)) + " TP2 " + str(round(tp2,2)) + " TP3 " + str(round(nh,2)))
        last_buy = now

    if prev > prev_v and curr < curr_v and curr < ll and now - last_sell > 1800:
        entry = curr - 0.6
        sl = shw + 0.5
        if sl - entry > 10:
            sl = entry + 9.5
        tp1 = entry - 6
        tp2 = entry - 11
        send("BEARISH BREAKDOWN\nENTRY " + str(round(entry,2)) + " SL " + str(round(sl,2)) + " TP1 " + str(round(tp1,2)) + " TP2 " + str(round(tp2,2)) + " TP3 " + str(round(nl,2)))
        last_sell = now

send("V6 PAXG ONLINE - BUY SELL WORKING")

while True:
    try:
        vals = get_candles()
        if not vals:
            time.sleep(60)
            continue
        closes = [x["close"] for x in vals]
        highs = [x["high"] for x in vals]
        lows = [x["low"] for x in vals]
        vidya = calc_vidya(closes)
        now_str = datetime.now().strftime("%H:%M")
        print(now_str + " Price " + str(closes[-1]) + " VIDYA " + str(vidya[-1]))
        check(closes, highs, lows, vidya)
        time.sleep(60)
    except Exception as e:
        print("Loop error", e)
        time.sleep(60)
