import os, time, requests
from datetime import datetime

def get_env_any(*names):
    all_env = {k.lower(): v for k,v in os.environ.items()}
    for n in names:
        if n.lower() in all_env:
            return all_env[n.lower()]
    return None

TOKEN = get_env_any("TOKEN","TELEGRAM_TOKEN","TELEGRAM_BOT_TOKEN","TELEGRA","TELEGRAM","BOT_TOKEN")
CHAT_ID = get_env_any("CHAT_ID","TELEGRAM_CHAT_ID")

print(f"TOKEN {bool(TOKEN)} CHAT {bool(CHAT_ID)} - NO API KEY MODE PAXG")

def send(msg):
    try:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": msg}, timeout=15)
        print("TG sent")
    except Exception as e:
        print(f"TG err {e}")

def get_candles():
    # Binance PAXGUSDT = GOLD price, no key needed
    try:
        url = "https://api.binance.com/api/v3/klines?symbol=PAXGUSDT&interval=5m&limit=100"
        data = requests.get(url, timeout=15).json()
        # data = [[openTime, open, high, low, close...],...]
        candles = []
        for d in data:
            candles.append({
                "open": float(d[1]),
                "high": float(d[2]),
                "low": float(d[3]),
                "close": float(d[4])
            })
        print(f"Got {len(candles)} PAXG candles price {candles[-1]['close']}")
        return candles
    except Exception as e:
        print(f"PAXG error {e}")
        return None

def calc_vidya(closes, period=20):
    v=[]
    for i in range(len(closes)):
        if i<period:
            v.append(closes[i]); continue
        up=sum(1 for k in range(i-period+1,i+1) if closes[k]>closes[k-1])
        down=period-up
        ch=abs(up-down)/(up+down) if up+down else 0
        alpha=0.2*ch
        v.append(closes[i]*alpha+v[-1]*(1-alpha))
    return v

last={"BUY":0,"SELL":0}
def check(closes,highs,lows,vidya):
    curr=closes[-1]; prev=closes[-2]; curr_v=vidya[-1]; prev_v=vidya[-2]
    lh=max(highs[-6:-1]); ll=min(lows[-6:-1]); slw=min(lows[-5:]); shw=max(highs[-5:])
    nh=max(highs[-20:])+1.5; nl=min(lows[-20:])-1.5
    now=time.time()
    if prev<prev_v and curr>curr_v and curr>lh and now-last["BUY"]>1800:
        entry=curr+0.6; sl=slw-0.5
        if entry-sl>10: sl=entry-9.5
        send(f"🔥 GOLD ONANA BULLISH VIDYA BOUNCE + BOS\nReclaim {prev_v:.2f}->{curr:.2f} Break {lh:.2f}\n\n✅ ENTRY: {entry:.2f} GOLD SPOT\n🛑 SL: {sl:.2f} (-${entry-sl:.1f})\n🎯 TP1: {entry+6:.2f} (+$6) 30%\n🎯 TP2: {entry+11:.2f} (+$11) 30%\n🎯 TP3: {nh:.2f} Liq\nPAXG Gold - No spam - No auto BE")
        last["BUY"]=now
    if prev>prev_v and curr<curr_v and curr<ll and now-last["SELL"]>1800:
        entry=curr-0.6; sl=shw+0.5
        if sl-entry>10: sl=entry+9.5
        send(f"🔥 GOLD ONANA BEARISH VIDYA BREAKDOWN\nBreak {prev_v:.2f}->{curr:.2f} Break {ll:.2f}\n\n❌ ENTRY: {entry:.2f} GOLD SPOT\n🛑 SL: {sl:.2f} (+${sl-entry:.1f})\n🎯 TP1: {entry-6:.2f} 30%\n🎯 TP2: {entry-11:.2f} 30%\n🎯 TP3: {nl:.2f} Liq\nPAXG Gold - No spam")
        last["SELL"]=now

send("✅ V6 BOT ONLINE - PAXG GOLD - NO API KEY NEEDED\nBUY + SELL WORKING - Will signal at 4157 bounce")

while True:
    try:
        vals=get_candles()
        if not vals:
            time.sleep(60); continue
        closes=[x["close"] for x in vals]; highs=[x["high"] for x in vals]; lows=[x["low"] for x in vals]
        vidya=calc_vidya(closes)
        print(f"{datetime.now().strftime('%H:%M')} Price {closes[-1]:.2f} VIDYA {vidya[-1]:.2f}")
        check(closes,highs,lows,vidya)
        time.sleep(60)
    except Exception as e:
        print(f"Loop {e}"); time.sleep(60)
