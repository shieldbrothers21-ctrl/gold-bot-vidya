import os, json, time, requests, yfinance as yf, pandas as pd

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT = os.getenv("CHAT_ID")
SYM = "GC=F"
FILE = "state.json"

def send(msg):
    try:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        data={"chat_id": CHAT, "text": msg, "parse_mode": "Markdown"})
    except Exception as e:
        print(e)

def load():
    try:
        with open(FILE, "r") as f:
            return json.load(f)
    except:
        return {"phase": None, "active": None}

def save(d):
    with open(FILE, "w") as f:
        json.dump(d, f)

def calc_vidya(s, p=14):
    diff = s.diff()
    pos = diff.clip(lower=0).rolling(p).sum()
    abs_sum = diff.abs().rolling(p).sum()
    cmo = 100 * (pos / abs_sum.replace(0, 1))
    k = cmo / 100
    v = 0
    out = []
    for i in range(len(s)):
        if i == 0:
            v = s.iloc[i]
        else:
            v = k.iloc[i] * s.iloc[i] + (1 - k.iloc[i]) * v
        out.append(v)
    return pd.Series(out, index=s.index)

def get_df(tf):
    df = yf.download(SYM, period="5d", interval=tf, progress=False, auto_adjust=True)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df['VIDYA'] = calc_vidya(df['Close'])
    return df

# START
send("✅ BOT 2 SMC VIDYA LIVE - 1H+15M+5M | BOS + DSL + Delta")

while True:
    try:
        st = load()
        df1h = get_df("1h")
        df15 = get_df("15m
