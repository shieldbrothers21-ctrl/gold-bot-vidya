import os, time, requests, yfinance as yf, pandas as pd, numpy as np, json
TOKEN=os.getenv("TELEGRAM_TOKEN"); CHAT=os.getenv("CHAT_ID"); SYM="GC=F"
SFILE="/tmp/state.json"
def send(m):
    try: requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id":CHAT,"text":m,"parse_mode":"Markdown"}, timeout=10)
    except: pass
def load():
    try: return json.load(open(SFILE))
    except: return {"phase":None, "active":None}
def save(s): json.dump(s, open(SFILE,"w"))
def calc_vidya(close, p=20, a=0.2):
    cmo=close.diff(p).abs().rolling(p).sum(); cmo2=close.diff(p).rolling(p).sum().abs()
    k=a*cmo2/cmo.replace(0,1)/100; v=[close.iloc[0]]
    for i in range(1,len(close)): v.append(close.iloc[i]*k.iloc[i]+v[-1]*(1-k.iloc[i]))
    return pd.Series(v, index=close.index)
def get_df(tf, period="5d"):
    df=yf.download(SYM, period=period, interval=tf, progress=False).dropna()
    if isinstance(df.columns, pd.MultiIndex): df.columns=df.columns.get_level_values(0)
    df['VIDYA']=calc_vidya(df['Close']); ema1=df['Close'].ewm(10).mean(); ema2=ema1.ewm(10).mean()
    df['DSL']=50+(ema1-ema2)/df['Close']*500; df['DSIG']=df['DSL'].ewm(3).mean()
    df['Delta']=pd.Series(np.where(df['Close']>df['Open'], df['Volume'], -df['Volume'])).rolling(20).sum()/df['Volume'].rolling(20).sum()*100
    return df
def analyze():
    df5=get_df("5m","3d"); df15=get_df("15m","5d"); df1h=get_df("60m","10d"); st=load()
    price=float(df5['Close'].iloc[-1]); high=float(df5['High'].iloc[-1]); low=float(df5['Low'].iloc[-1])
    v5=float(df5['VIDYA'].iloc[-1]); v15=float(df15['VIDYA'].iloc[-1]); v1h=float(df1h['VIDYA'].iloc[-1])
    dsl=float(df5['DSL'].iloc[-1]); dsig=float(df5['DSIG'].iloc[-1]); delta=float(df5['Delta'].iloc[-1])
    bsl=float(df15['High'].tail(20).max()); ssl=float(df15['Low'].tail(20).min())
    bsl_1h=float(df1h['High'].tail(20).max()); ssl_1h=float(df1h['Low'].tail(20).min())
    # TRACK ACTIVE TRADE
    if st.get("active"):
        tr=st["active"]; e=tr["entry"]; sl=tr["sl"]; tp1=tr["tp1"]; tp2=tr["tp2"]; side=tr["side"]
        if side=="SHORT":
            if low <= tp1 and not tr.get("tp1_hit"):
                tr["tp1_hit"]=True; st["active"]=tr; save(st)
                return f"💰 *TP1 HIT!* SHORT {e:.2f} -> TP1 {tp1:.2f} HIT! ✅\nPrice {price:.2f}\n✅ Book 50% | SL to BE | Hold for TP2 {tp2:.2f}"
            if low <= tp2:
                save({"phase":None,"active":None})
                return f"💰💰 *TP2 HIT! FULL TP!* 🔥🔥\nSHORT {e:.2f} -> TP2 {tp2:.2f} HIT! ✅✅\n1H+15M+5M Scalp Done!"
            if high >= sl:
                save({"phase":None,"active":None})
                return f"❌ *SL HIT* SHORT {e:.2f} -> SL {sl:.2f} Hit\nLoss {(sl-e):.2f}$"
        else:
            if high >= tp1 and not tr.get("tp1_hit"):
                tr["tp1_hit"]=True; st["active"]=tr; save(st)
                return f"💰 *TP1 HIT!* LONG {e:.2f} -> TP1 {tp1:.2f} HIT! ✅\n✅ Book 50% | SL to BE | Hold for TP2 {tp2:.2f}"
            if high >= tp2:
                save({"phase":None,"active":None})
                return f"💰💰 *TP2 HIT! FULL TP!* 🔥🔥\nLONG {e:.2f} -> TP2 {tp2:.2f} HIT! ✅✅"
            if low <= sl:
                save({"phase":None,"active":None})
                return f"❌ *SL HIT* LONG {e:.2f} -> SL {sl:.2f} Hit\nLoss {(e-sl):.2f}$"
    # ANALYSIS LIKE YOUR SCREENSHOTS
    below_all=price < v1h and price < v15 and price < v5
    above_all=price > v1h and price > v15 and price > v5
    bearish_dsl=dsl < 50 and dsl < dsig; bullish_dsl=dsl > 50 and dsl > dsig
    bos_down=df5['Close'].iloc[-1] < df5['Low'].iloc[-6:-1].min()
    bos_up=df5['Close'].iloc[-1] > df5['High'].iloc[-6:-1].max()
    # SHORT - Valid Continuation - All timeframes bearish
    if below_all and bearish_dsl and bos_down and delta < -5:
        entry=price; sl=round(bsl+3,2); tp1=round(ssl,2); tp2=round(ssl_1h,2)
        st["active"]={"side":"SHORT","entry":entry,"sl":sl,"tp1":tp1,"tp2":tp2,"tp1_hit":False}; save(st)
        return f"🔴 *XAUUSD SHORT - 1H+15M+5M VALID*\n1H VIDYA {v1h:.2f} Bearish | 15M VIDYA {v15:.2f} Bearish | 5M VIDYA {v5:.2f} Bearish\nBSL 15M {bsl:.2f} swept | BOS 5M DOWN | DSL {dsl:.1f} below 50 | Delta {delta:.1f}% SELL\nENTRY SHORT @ {entry:.2f}\nSL {sl:.2f} Above 15M OB (Small 3-4$)\nTP1 {tp1:.2f} 15M SSL (Scalp)\nTP2 {tp2:.2f} 1H SSL (Runner)\nInstruction: Book 50% TP1, SL to BE, Hold 0.02 for TP2\nBot tracks TP1/TP2/SL HIT!"
    # LONG - Scalp Reversal - All timeframes bullish
    if above_all and bullish_dsl and bos_up and delta > 5:
        entry=price; sl=round(ssl-3,2); tp1=round(bsl,2); tp2=round(bsl_1h,2)
        st["active"]={"side":"LONG","entry":entry,"sl":sl,"tp1":tp1,"tp2":tp2,"tp1_hit":False}; save(st)
        return f"🟢 *XAUUSD LONG - 1H+15M+5M SCALP REVERSAL*\
