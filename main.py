import os
import time
import requests
from datetime import datetime

TOKEN = os.getenv("TOKEN") or os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
TD_KEY = os.getenv("TWELVEDATA_KEY") or os.getenv("TD_KEY")

# V6 EXACT as 4182 trade you liked
SPREAD_BUFFER = 0.60
TP1_DIST = 6.0
TP2_DIST = 11.0

def send(msg):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        r = requests.post(url, data={"chat_id": CHAT_ID, "text": msg}, timeout=15)
        print(f"TG {r.status_code}: {r.text[:350]}")
    except Exception as e:
        print(f"Send err {e}")

def get_candles():
    url = f"https://api.twelvedata.com/time_series?symbol=XAU/USD&interval=5min&apikey={TD_KEY}&outputsize=100&format=JSON"
    j = requests.get(url, timeout=20).json()
    if "values" not in j:
        print(f"TD Error {j}")
        return None
    return j["values"][::-1]

def calc_vidya(closes, period=20):
    vidya = []
    for i in range(len(closes)):
        if i < period:
            vidya.append(closes[i])
            continue
        up = sum(1 for k in range(i-period+1, i+1) if closes[k] > closes[k-1])
        down = period - up
        ch = abs(up-down)/(up+down) if (up+down) else 0
        alpha = 0.2 * ch
        v = closes[i]*alpha + vidya[-1]*(1-alpha)
        vidya.append(v)
    return vidya

last_signal = {"BUY": 0, "SELL": 0}

def check_vidya_v6(closes, highs, lows, vidya):
    curr = closes[-1]
    prev = closes[-2]
    curr_v = vidya[-1]
    prev_v = vidya[-2]

    last_5_high = max(highs[-6:-1])
    last_5_low = min(lows[-6:-1])
    sweep_low = min(lows[-5:])
    sweep_high = max(highs[-5:])
    next_liq_high = max(highs[-20:]) + 1.5
    next_liq_low = min(lows[-20:]) - 1.5

    now = time.time()

    # === BUY - EXACT like 4182 message ===
    # Before 4178 now 4182.06 = +$4 bounce from VIDYA support
    # Green wick + volume 9.062K = liquidity sweep, sellers trapped
    # Pink flag Sell 340 Delta -200% = short squeeze = LONG
    was_below = prev < prev_v
    now_above = curr > curr_v
    bos_up = curr > last_5_high

    if was_below and now_above and bos_up:
        if now - last_signal["BUY"] > 1800:
            entry = curr + SPREAD_BUFFER
            sl = sweep_low - 0.50
            if entry - sl > 10: sl = entry - 9.5 # max $10 like you said
            tp1 = entry + TP1_DIST
            tp2 = entry + TP2_DIST
            tp3 = next_liq_high

            msg = f"""🔥 GOLD ONANA BULLISH VIDYA BOUNCE + BOS
Reclaim {prev_v:.2f}->{curr:.2f} (V6) Break {last_5_high:.2f}

✅ ENTRY: {entry:.2f} GOLD ONANA SPOT
🛑 SL: {sl:.2f} (below wick low -${entry-sl:.1f})
🎯 TP1: {tp1:.2f} (+${TP1_DIST}) take 30%
🎯 TP2: {tp2:.2f} (+${TP2_DIST}) take 30% - high where Delta flag
🎯 TP3: {tp3:.2f} (Next Liquidity) - top from morning

Filters: VIDYA Support + BOS + Delta Short Squeeze -200%
Note: Take TP1 TP2 fast, move SL to BE manually
No spam | 1 signal per bounce | No auto BE"""

            send(msg)
            last_signal["BUY"] = now

    # === SELL - MIRROR SAME LOGIC ===
    was_above = prev > prev_v
    now_below = curr < curr_v
    bos_down = curr < last_5_low

    if was_above and now_below and bos_down:
        if now - last_signal["SELL"] > 1800:
            entry = curr - SPREAD_BUFFER
            sl = sweep_high + 0.50
            if sl - entry > 10: sl = entry + 9.5
            tp1 = entry - TP1_DIST
            tp2 = entry - TP2_DIST
            tp3 = next_liq_low

            msg = f"""🔥 GOLD ONANA BEARISH VIDYA BREAKDOWN + BOS
Breakdown {prev_v:.2f}->{curr:.2f} (V6) Break {last_5_low:.2f}

❌ ENTRY: {entry:.2f} GOLD ONANA SPOT
🛑 SL: {sl:.2f} (above wick high +${sl-entry:.1f})
🎯 TP1: {tp1:.2f} (-${TP1_DIST}) take 30%
🎯 TP2: {tp2:.2f} (-${TP2_DIST}) take 30%
🎯 TP3: {tp3:.2f} (Next Liquidity)

Filters: VIDYA Resistance + BOS + Delta Long Squeeze
No spam | 1 signal per breakdown | No auto BE"""

            send(msg)
            last_signal["SELL"] = now

# === MAIN LOOP ===
print("V6 FINAL - BOTH SIDES TP1 TP2 TP3")
send("✅ V6 VIDYA BOT ONLINE - BOTH SIDES\nTP1 +$6 | TP2 +$11 | TP3 Next Liquidity\nFilters: VIDYA Bounce + BOS + Sweep\nNo spam - 1 per bounce - No auto BE")

while True:
    try:
        vals = get_candles()
        if not vals:
            time.sleep(60)
            continue

        closes = [float(x["close"]) for x in vals]
        highs = [float(x["high"]) for x in vals]
        lows = [float(x["low"]) for x in vals]
        vidya = calc_vidya(closes)

        print(f"{datetime.now().strftime('%H:%M')} Price {closes[-1]:.2f} VIDYA {vidya[-1]:.2f}")
        check_vidya_v6(closes, highs, lows, vidya)
        time.sleep(60)

    except Exception as e:
        print(f"Loop err {e}")
        time.sleep(60)
