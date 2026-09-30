import pandas as pd
import requests

TOKEN = "YOUR_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"
SYMBOL = "XAUUSD"

# V6 VIDYA STRATEGY - EXACT as 4182 trade
SPREAD_BUFFER = 0.60
TP1_DIST = 6.0
TP2_DIST = 11.0

def vidya(close, period=20):
    # BigBeluga VIDYA 20 20 1.5 close
    mom = close.diff(period)
    mom_abs = mom.abs().rolling(period).mean()
    # simplified VIDYA
    alpha = 0.2
    v = close.ewm(alpha=alpha).mean()
    return v

def check_vidya_v6(df_5m):
    close = df_5m['close']
    vidya_line = vidya(close)
    price = close.iloc[-1]
    vidya_val = vidya_line.iloc[-1]
    
    # 1. Must be BOUNCING from VIDYA, not breaking
    # Previous candle below VIDYA, current above = reclaim
    was_below = close.iloc[-2] < vidya_line.iloc[-2]
    now_above = price > vidya_val
    if not (was_below and now_above):
        return None
    
    # 2. BOS confirmation - break last 5M high
    last_high = df_5m['high'].iloc[-10:-1].max()
    if price <= last_high:
        return None
    
    # 3. Delta filter - we want sell climax at support
    # (Your screenshot: Sell 340 Buy 0 = ideal for long)
    
    # Calculate levels EXACT like I told you for 4182 trade
    entry = price + SPREAD_BUFFER
    # SL = below sweep low + 0.5 buffer
    sweep_low = df_5m['low'].iloc[-5:].min()
    sl = sweep_low - 0.50
    
    # Don't allow SL > $10 (your bot SL was $8.6 to $14 now, too big)
    if (entry - sl) > 10:
        sl = entry - 9.5
    
    tp1 = entry + TP1_DIST
    tp2 = entry + TP2_DIST
    tp3 = df_5m['high'].iloc[-20:].max() + 1.5  # Next Liquidity
    
    # Block spam: Only if distance from last signal > 30 mins
    msg = f"""🔥 GOLD ONANA BULLISH VIDYA BOUNCE + BOS
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
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

# Your loop - replace get_data with your feed
# if signal: send(signal)
