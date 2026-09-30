import pandas as pd
import requests
import os
import time
import yfinance as yf

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
SYMBOL = "GC=F" # use GC=F for gold

# V6 VIDYA STRATEGY - EXACT as 4182 trade
SPREAD_BUFFER = 0.60
TP1_DIST = 6.0
TP2_DIST = 11.0

def vidya(close, period=20):
    mom = close.diff(period)
    mom_abs = mom.abs().rolling(period).mean()
    alpha = 0.2
    v = close.ewm(alpha=alpha).mean()
    return v

def check_vidya_v6(df_5m):
    close = df_5m['close']
    vidya_line = vidya(close)
    price = close.iloc[-1]
    vidya_val = vidya_line.iloc[-1]

    was_below = close.iloc[-2] < vidya_line.iloc[-2]
    now_above = price > vidya_val
    if not (was_below and now_above):
        return None

    last_high = df_5m['high'].iloc[-10:-1].max()
    if price <= last_high:
        return None

    entry = price + SPREAD_BUFFER
    sweep_low = df_5m['low'].iloc[-5:].min()
    sl = sweep_low - 0.50

    if (entry - sl) > 10:
        sl = entry - 9.5

    tp1 = entry + TP1_DIST
    tp2 = entry + TP2_DIST
    tp3 = df_5m['high'].iloc[-20:].max() + 1.5

    msg = f"""🔥 GOLD VIDYA BOUNCE + BOS
Reclaim {vidya_val:.2f}->{price:.2f} (V6)

✅ ENTRY: {entry:.2f} GOLD SPOT
🛑 SL: {sl:.2f}
🎯 TP1: {tp1:.2f} (+${TP1_DIST})
🎯 TP2: {tp2:.2f} (+${TP2_DIST})
🎯 TP3: {tp3:.2f} (Next Liquidity)

Filters: VIDYA Support + BOS + Delta Short Squeeze
No spam | 1 signal per bounce | No auto BE
"""
    return msg

def send(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg}, timeout=10)
    except Exception as e:
        print(f"Telegram error: {e}")

# --- BOT START ---
print("V6 BOT STARTING")
send("✅ V6 VIDYA BOT ONLINE - Fixed TOKEN - Waiting for 4182 bounce")

last_signal_time = 0

while True:
    try:
        df = yf.download(SYMBOL, period="2d", interval="5m", progress=False)
        if len(df) < 30:
            time.sleep(60)
            continue

        # flatten yfinance columns
        df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
        df.rename(columns={"Close":"close","High":"high","Low":"low"}, inplace=True)
        df.columns = [c.lower() for c in df.columns]

        signal = check_vidya_v6(df)
        if signal:
            now = time.time()
            if now - last_signal_time > 1800: # 30 min anti-spam
                send(signal)
                last_signal_time = now
                print("Signal sent")

        time.sleep(60)
    except Exception as e:
        print(f"Loop error: {e}")
        time.sleep(60)
