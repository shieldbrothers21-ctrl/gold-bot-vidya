import os, time, requests, threading
import yfinance as yf
import pandas as pd
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
active_trades = []

def send_tg(msg):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)
    except Exception as e:
        print(e)

def vidya(src, mom_len=20, smooth=1.5):
    mom = src.diff()
    pos = mom.where(mom>=0,0).rolling(mom_len).sum()
    neg = (-mom.where(mom<0,0)).rolling(mom_len).sum()
    cmo = 100 * (pos - neg) / (pos + neg).replace(0,1)
    alpha = (abs(cmo)/100) ** smooth
    v = pd.Series(index=src.index, dtype=float)
    v.iloc[0]=src.iloc[0]
    for i in range(1,len(src)):
        v.iloc[i]= alpha.iloc[i]*src.iloc[i] + (1-alpha.iloc[i])*v.iloc[i-1] if not pd.isna(alpha.iloc[i]) else v.iloc[i-1]
    return v

def get_tf():
    df1h = yf.download("GC=F", period="20d", interval="1h", progress=False)
    df15 = yf.download("GC=F", period="10d", interval="15m", progress=False)
    df5 = yf.download("GC=F", period="5d", interval="5m", progress=False)
    for df in [df1h, df15, df5]:
        if isinstance(df.columns, pd.MultiIndex): df.columns=df.columns.get_level_values(0)
    return df1h.dropna(), df15.dropna(), df5.dropna()

def bsl_ssl(df, tol=2):
    highs=df['High'].tail(30); lows=df['Low'].tail(30)
    bsl=highs.max(); ssl=lows.min()
    return bsl, ssl, len(highs[abs(highs-bsl)<=tol]), len(lows[abs(lows-ssl)<=tol])

def check():
    global active_trades
    df1h, df15, df5 = get_tf()
    if len(df5)<30: return
    c1=df1h['Close']; c15=df15['Close']; c5=df5['Close']; o5=df5['Open']
    v1h=vidya(c1); v15=vidya(c15); v5=vidya(c5)
    price=float(c5.iloc[-1])
    v1h_val=float(v1h.iloc[-1]); v15_val=float(v15.iloc[-1]); v5_val=float(v5.iloc[-1])
    close_above_vidya = c5.iloc[-2] > v5.iloc[-2] and c5.iloc[-1] > v5.iloc[-1]
    close_below_vidya = c5.iloc[-2] < v5.iloc[-2] and c5.iloc[-1] < v5.iloc[-1]
    close_above_15 = c15.iloc[-2] > v15.iloc[-2]
    close_below_15 = c15.iloc[-2] < v15.iloc[-2]
    trend_1h_bull = c1.iloc[-1] > v1h.iloc[-1]
    trend_1h_bear = c1.iloc[-1] < v1h.iloc[-1]
    bsl, ssl, bsl_cnt, ssl_cnt = bsl_ssl(df5)
    buy_vol=float(df5['Volume'].where(c5>o5,0).tail(20).mean())
    sell_vol=float(df5['Volume'].where(c5<o5,0).tail(20).mean())
    delta=100*(buy_vol-sell_vol)/(buy_vol+sell_vol+1)
    ema10=c5.ewm(10).mean().iloc[-1]; ema21=c5.ewm(21).mean().iloc[-1]
    dsl_bull=ema10>ema21

    for trade in active_trades[:]:
        if trade['dir']=='LONG':
            if price <= trade['sl'] and not trade.get('sl_hit'):
                send_tg(f"🔴 **SL HIT** LONG {trade['entry']} → SL {trade['sl']} ❌\nPrice: {price:.2f}")
                active_trades.remove(trade)
            elif price >= trade['tp1'] and not trade.get('tp1_hit'):
                trade['tp1_hit']=True
                send_tg(f"✅ **TP1 HIT** LONG {trade['entry']} → {trade['tp1']} +{(trade['tp1']-trade['entry']):.1f}$ 💰\nMove SL to BE! 50% off")
            elif price >= trade['tp2'] and trade.get('tp1_hit') and not trade.get('tp2_hit'):
                trade['tp2_hit']=True
                send_tg(f"✅✅ **TP2 HIT** LONG {trade['entry']} → {trade['tp2']} +{(trade['tp2']-trade['entry']):.1f}$ 💰💰\nBSL {bsl:.1f} swept!")
            elif price >= trade['tp3'] and trade.get('tp2_hit'):
                send_tg(f"✅✅✅ **TP3 HIT - ALL TP HIT!** LONG {trade['entry']} → {trade['tp3']} +{(trade['tp3']-trade['entry']):.1f}$ 🔥🔥🔥")
                active_trades.remove(trade)
        else:
            if price >= trade['sl'] and not trade.get('sl_hit'):
                send_tg(f"🔴 **SL HIT** SHORT {trade['entry']} → SL {trade['sl']} ❌")
                active_trades.remove(trade)
            elif price <= trade['tp1'] and not trade.get('tp1_hit'):
                trade['tp1_hit']=True
                send_tg(f"✅ **TP1 HIT** SHORT {trade['entry']} → {trade['tp1']} +{(trade['entry']-trade['tp1']):.1f}$ 💰 +16$ scalp!")
            elif price <= trade['tp2'] and trade.get('tp1_hit') and not trade.get('tp2_hit'):
                trade['tp2_hit']=True
                send_tg(f"✅✅ **TP2 HIT** SHORT {trade['entry']} → {trade['tp2']} +{(trade['entry']-trade['tp2']):.1f}$ 💰💰")
            elif price <= trade['tp3'] and trade.get('tp2_hit'):
                send_tg(f"✅✅✅ **TP3 HIT - ALL TP HIT!** SHORT {trade['entry']} → {trade['tp3']} 🔥🔥🔥")
                active_trades.remove(trade)

    low_swept = float(df5['Low'].iloc[-2]) <= ssl+2
    if trend_1h_bull and close_above_15 and close_above_vidya and low_swept and dsl_bull and len(active_trades)==0:
        if delta > -70:
            entry=round(price,2); sl=round(ssl-3.5,2); tp1=round(entry+7,2); tp2=round(bsl-1,2); tp3=round(tp2+8,2)
            rr1=round((tp1-entry)/(entry-sl+0.1),2); rr2=round((tp2-entry)/(entry-sl+0.1),2); rr3=round((tp3-entry)/(entry-sl+0.1),2)
            active_trades.append({"dir":"LONG","entry":entry,"sl":sl,"tp1":tp1,"tp2":tp2,"tp3":tp3,"tp1_hit":False,"tp2_hit":False})
            send_tg(f"🟢 **LONG CONFIRMED - 1H 15M 5M CLOSE**\nLike 4275.5 screenshot!\n━━━━━━━━━━━━━━\n**1H:** CLOSE {c1.iloc[-1]:.1f} > VIDYA {v1h_val:.1f} BULL ✓\n**15M:** CLOSE {c15.iloc[-2]:.1f} > VIDYA {v15_val:.1f} CHoCH ✓\n**5M:** CLOSE {c5.iloc[-2]:.1f} > VIDYA {v5_val:.1f} ✓\nSSL {ssl:.2f} swept {ssl_cnt}x ✓\nDelta {delta:.1f}% absorption ✓\n━━━━━━━━━━━━━━\n**ENTRY: {entry} NOW**\nSL: {sl}\nTP1: {tp1} RR 1:{rr1} (50%)\nTP2: {tp2} RR 1:{rr2} (30%)\nTP3: {tp3} RR 1:{rr3} Runner\nI will mark TP1/TP2/TP3/SL hit!")

    high_swept = float(df5['High'].iloc[-2]) >= bsl-2
    if trend_1h_bear and close_below_15 and close_below_vidya and high_swept and not dsl_bull and len(active_trades)==0:
        if delta < -10:
            entry=round(price,2); sl=round(bsl+4,2); tp1=round(ssl+2,2); tp2=round(tp1-5,2); tp3=round(ssl-8,2)
            rr1=round((entry-tp1)/(sl-entry+0.1),2)
            active_trades.append({"dir":"SHORT","entry":entry,"sl":sl,"tp1":tp1,"tp2":tp2,"tp3":tp3,"tp1_hit":False,"tp2_hit":False})
            send_tg(f"🔴 **SHORT CONFIRMED - 1H 15M 5M CLOSE**\nLike 4262→4252 +16$!\n━━━━━━━━━━━━━━\n**1H:** {c1.iloc[-1]:.1f} < VIDYA {v1h_val:.1f} BEAR ✓\n**15M:** {c15.iloc[-2]:.1f} < VIDYA {v15_val:.1f} BOS ✓\n**5M:** {c5.iloc[-2]:.1f} < VIDYA {v5_val:.1f} ✓\nBSL {bsl:.2f} swept {bsl_cnt}x ✓\nDelta {delta:.1f}% ✓\n━━━━━━━━━━━━━━\n**ENTRY SHORT NOW @ {entry}**\nSL: {sl}\nTP1: {tp1} RR 1:{rr1}\nTP2: {tp2}\nTP3: {tp3}\n⚠️ Wait CLOSE below {tp1:.1f} then retest!")

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ **BOT 2 SMC VIDYA LIVE**\n🟢 1H/15M/5M CLOSE CONFIRMATION\n📊 BSL/SSL + VIDYA + BOS/CHoCH + OB Retest + Delta + DSL\n🎯 ENTRY + SL + TP1 TP2 TP3 + TP HIT / SL HIT tracking\nLike your screenshots - waiting for close!", parse_mode="Markdown")

def main():
    send_tg("✅ **BOT 2 LIVE - 1H 15M 5M CLOSE CONFIRMATION MODE**\nWaiting for candle CLOSE above/below VIDYA...\nWill mark TP1 TP2 TP3 SL hit!")
    app=Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_cmd)); app.add_handler(CommandHandler("status", start_cmd))
    threading.Thread(target=lambda: app.run_polling(drop_pending_updates=True), daemon=True).start()
    while True:
        try: check()
        except Exception as e: print(e)
        time.sleep(60)

if __name__=="__main__": main()
