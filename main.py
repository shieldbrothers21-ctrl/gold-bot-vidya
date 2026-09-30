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

print("V7 REAL XAUUSD MODE")

def send(msg):
    try:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": msg}, timeout=15)
        print("TG sent")
    except Exception as e:
        print(e)

def get_candles():
    # Yahoo XAUUSD real spot - no key, same as your broker
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        url = "https://query1.finance.yahoo.com/v8/finance/chart/XAUUSD=X?interval=5m&range=2d"
        r = requests.get(url, headers=headers, timeout=15)
        print("Yahoo status", r.status_code)
        j = r.json()
        result = j["chart"]["result"][0]
        opens = result["indicators"]["quote"][0]["open"]
        highs = result["indicators"]["quote"][0]["high"]
        lows = result["indicators"]["quote"][0]["low"]
        closes = result["indicators"]["quote"][0]["close"]
        candles = []
        for i in range(len(closes)):
            if closes[i] is None: continue
            candles.append({
                "open": float(opens[i]),
                "high": float(highs[i]),
                "low": float(lows[i]),
                "close": float(closes[i])
            })
        candles = candles[-100:]
        print(f"Got {len(candles)} XAU candles price {candles[-1]['close']}")
        return candles
    except Exception as e:
        print("Yahoo fail", e)
        # fallback to PAXG if Yahoo blocked
        try:
            url2 = "https://data-api.binance.vision/api/v3/klines?symbol=PAXGUSDT&interval=5m&limit=100"
            r2 = requests.get(url2, headers=headers, timeout=15)
            data = r2.json()
            candles = []
            for d in data:
                candles.append({"open": float(d[1]), "high": float(d[2]), "low": float(d[3]), "close": float(d[4])-10})
            print(f"Fallback PAXG-10 price {candles[-1]['close']}")
            return candles
        except Exception as e2:
            print("Fallback fail", e2)
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
        send(f"🔥 GOLD ONANA BULLISH VIDYA BOUNCE + BOS\nReclaim {prev_v:.2f}->{curr:.2f} Break {lh:.2f}\n\n✅ ENTRY: {entry:.2f} [0.03->0.02]\n🛑 SL: {sl:.2f} (-${entry-sl:.1f})\n🎯 TP1: {entry+6:.2f} (+$6) CLOSE 0.03\n🎯 TP2: {entry+11:.2f} (+$11) CLOSE 0.02\n🎯 TP3: {nh:.2f} LIQ RUNNER 0.02")
        last_buy = now

    if prev > prev_v and curr < curr_v and curr < ll and now - last_sell > 1800:
        entry = curr - 0.6
        sl = shw + 0.5
        if sl - entry > 10:
            sl = entry + 9.5
        send(f"🔥 GOLD ONANA BEARISH BREAKDOWN\nBreak {prev_v:.2f}->{curr:.2f} Break {ll:.2f}\n\n❌ ENTRY: {entry:.2f} [0.03->0.02]\n🛑 SL: {sl:.2f}\n🎯 TP1: {entry-6:.2f} (-$6) CLOSE 0.03\n🎯 TP2: {entry-11:.2f} (-$11) CLOSE 0.02\n🎯 TP3: {nl:.2f} LIQ RUNNER 0.02")
        last_sell = now

send("✅ V7 REAL XAUUSD ONLINE\nSame price as cTrader 4159\nTP1 +$6 TP2 +$11 TP3 LIQ")

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
        print(now_str + " Price " + str(round(closes[-1],2)) + " VIDYA " + str(round(vidya[-1],2)))
        check(closes, highs, lows, vidya)
        time.sleep(60)
    except Exception as e:
        print("Loop error", e)
        time.sleep(60)
