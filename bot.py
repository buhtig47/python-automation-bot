import ccxt
import pandas as pd
import pandas_ta as ta
import requests
import time
import schedule
from datetime import datetime

# ============================================================
# APNI SETTINGS YAHAN DALO
# ============================================================
TELEGRAM_TOKEN   = ""
TELEGRAM_CHAT_ID = ""

# Scan Settings
RSI_ENTRY_MIN          = 35
RSI_ENTRY_MAX          = 60
RSI_EXIT               = 70
LEVERAGE_SUGGESTION    = 10
SCAN_INTERVAL_MINUTES  = 15
BTC_CRASH_THRESHOLD    = -5.0   # BTC -5% gire toh emergency alert
VOLUME_SPIKE_MULTIPLIER = 2.0   # Volume 2x average se zyada = spike

# ============================================================
# 100+ TOP COINS
# ============================================================
TOP_COINS = [
    # Tier 1 - Highest Volume
    'BTC/USDT','ETH/USDT','BNB/USDT','SOL/USDT','XRP/USDT',
    'DOGE/USDT','ADA/USDT','AVAX/USDT','LINK/USDT','DOT/USDT',
    # Tier 2 - High Volume
    'MATIC/USDT','LTC/USDT','UNI/USDT','ATOM/USDT','ETC/USDT',
    'BCH/USDT','APT/USDT','OP/USDT','ARB/USDT','SUI/USDT',
    # Tier 3 - Good Volume
    'TRX/USDT','TON/USDT','INJ/USDT','FIL/USDT','NEAR/USDT',
    'AAVE/USDT','FTM/USDT','ALGO/USDT','SAND/USDT','MANA/USDT',
    'GALA/USDT','ENJ/USDT','CHZ/USDT','HOT/USDT','VET/USDT',
    'THETA/USDT','EOS/USDT','XLM/USDT','HBAR/USDT','ICP/USDT',
    'RUNE/USDT','EGLD/USDT','FLOW/USDT','XTZ/USDT','AXS/USDT',
    'ROSE/USDT','ZIL/USDT','ONE/USDT','KSM/USDT','WAVES/USDT',
    # Tier 4 - Medium Volume
    'GMT/USDT','GAL/USDT','APE/USDT','LDO/USDT','MASK/USDT',
    'DYDX/USDT','CRV/USDT','SNX/USDT','1INCH/USDT','BAL/USDT',
    'COMP/USDT','MKR/USDT','YFI/USDT','SUSHI/USDT','GRT/USDT',
    'ENS/USDT','IMX/USDT','BLUR/USDT','PEPE/USDT','WLD/USDT',
    'SEI/USDT','TIA/USDT','PYTH/USDT','JTO/USDT','MEME/USDT',
    'ORDI/USDT','SATS/USDT','STX/USDT','CFX/USDT','ACH/USDT',
    'HIGH/USDT','HOOK/USDT','AMB/USDT','LQTY/USDT','SSV/USDT',
    'MAGIC/USDT','GMX/USDT','RDNT/USDT','ARK/USDT','ID/USDT',
    'EDU/USDT','SXP/USDT','RAD/USDT','BICO/USDT','AGLD/USDT',
    'OGN/USDT','WRX/USDT','BETA/USDT','CHESS/USDT','DAR/USDT',
    'JASMY/USDT','ACM/USDT','ATA/USDT','CYBER/USDT','FRONT/USDT'
]

# ============================================================
# TELEGRAM
# ============================================================

def send_telegram(message):
    url     = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code == 200:
            print("✅ Telegram sent!")
        else:
            print(f"❌ Telegram: {r.text}")
    except Exception as e:
        print(f"❌ Telegram error: {e}")

# ============================================================
# BINANCE
# ============================================================

def get_exchange():
    return ccxt.binance({
        'options': {'defaultType': 'future'},
        'enableRateLimit': True,
    })

# ============================================================
# BTC CRASH MONITOR
# ============================================================

btc_last_crash_alert = 0

def check_btc_crash(exchange):
    global btc_last_crash_alert
    try:
        ticker = exchange.fetch_ticker('BTC/USDT')
        change = ticker.get('percentage', 0) or 0
        price  = ticker.get('last', 0) or 0

        if change <= BTC_CRASH_THRESHOLD:
            if time.time() - btc_last_crash_alert > 3600:
                btc_last_crash_alert = time.time()
                msg = f"""
🚨🚨 <b>BTC CRASH ALERT!</b> 🚨🚨
━━━━━━━━━━━━━━━━━━━
💥 BTC: ${price}
📉 Change: {change:.2f}%
⚠️ <b>APNE BOTS CHECK KARO!</b>
⚠️ <b>HIGH LEVERAGE POSITIONS RISK MEIN!</b>
🕐 {datetime.now().strftime('%H:%M:%S')}
━━━━━━━━━━━━━━━━━━━
❗ Liquidation risk badh gaya hai!"""
                send_telegram(msg)
                print(f"🚨 BTC CRASH ALERT! {change:.2f}%")
        return change, price
    except Exception as e:
        print(f"❌ BTC check error: {e}")
        return 0, 0

# ============================================================
# MARKET DATA
# ============================================================

def get_coins_data(exchange):
    coins = []
    print(f"📊 Fetching {len(TOP_COINS)} coins...")

    for symbol in TOP_COINS:
        try:
            ticker = exchange.fetch_ticker(symbol)
            price  = ticker.get('last', 0) or 0
            volume = ticker.get('quoteVolume', 0) or 0
            change = ticker.get('percentage', 0) or 0

            if price > 0:
                coins.append({
                    'symbol': symbol,
                    'price':  price,
                    'volume': volume,
                    'change': change
                })
                print(f"  ✅ {symbol}: ${price} | Vol: ${volume:,.0f}")
            time.sleep(0.15)
        except:
            continue

    print(f"✅ Total: {len(coins)} coins ready!")
    return coins

# ============================================================
# VOLUME SPIKE DETECTION
# ============================================================

volume_history = {}

def check_volume_spike(symbol, current_volume):
    history = volume_history.get(symbol, [])
    if len(history) >= 3:
        avg_vol = sum(history[-3:]) / 3
        if avg_vol > 0 and current_volume > avg_vol * VOLUME_SPIKE_MULTIPLIER:
            volume_history[symbol] = history[-3:] + [current_volume]
            return True, round(current_volume / avg_vol, 1)
    volume_history[symbol] = history[-3:] + [current_volume]
    return False, 0

# ============================================================
# TECHNICAL ANALYSIS
# ============================================================

def get_ohlcv(exchange, symbol, timeframe, limit=100):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        if not ohlcv or len(ohlcv) < 50:
            return None
        df = pd.DataFrame(ohlcv, columns=['timestamp','open','high','low','close','volume'])
        return df
    except:
        return None

def calc_indicators(df):
    if df is None or len(df) < 50:
        return None
    try:
        df             = df.copy()
        df['rsi_14']   = ta.rsi(df['close'], length=14)
        df['ema_20']   = ta.ema(df['close'], length=20)
        df['ema_50']   = ta.ema(df['close'], length=50)
        df['vol_ma']   = df['volume'].rolling(window=10).mean()
        return df
    except:
        return None

def analyze_coin(exchange, symbol, price, volume):
    try:
        df_15m = calc_indicators(get_ohlcv(exchange, symbol, '15m'))
        df_1h  = calc_indicators(get_ohlcv(exchange, symbol, '1h'))
        df_4h  = calc_indicators(get_ohlcv(exchange, symbol, '4h'))

        if df_15m is None or df_1h is None or df_4h is None:
            return None

        rsi_15m  = round(float(df_15m['rsi_14'].iloc[-1]), 2)
        rsi_1h   = round(float(df_1h['rsi_14'].iloc[-1]), 2)
        rsi_4h   = round(float(df_4h['rsi_14'].iloc[-1]), 2)
        ema20    = float(df_1h['ema_20'].iloc[-1])
        ema50    = float(df_1h['ema_50'].iloc[-1])
        vol_now  = float(df_1h['volume'].iloc[-1])
        vol_avg  = float(df_1h['vol_ma'].iloc[-1])

        support    = round(float(df_4h['low'].tail(20).min()) * 0.99, 6)
        resistance = round(float(df_4h['high'].tail(20).max()) * 1.01, 6)

        # Score
        score = 0
        if RSI_ENTRY_MIN <= rsi_15m <= RSI_ENTRY_MAX: score += 15
        if RSI_ENTRY_MIN <= rsi_1h  <= RSI_ENTRY_MAX: score += 15
        if RSI_ENTRY_MIN <= rsi_4h  <= RSI_ENTRY_MAX: score += 10
        if price > ema20:                              score += 15
        if ema20 > ema50:                              score += 15
        if vol_avg > 0 and vol_now > vol_avg:          score += 30

        # Volume spike
        is_spike, spike_x = check_volume_spike(symbol, volume)
        if is_spike:
            score += 10

        liq_price = round(price * (1 - (1/LEVERAGE_SUGGESTION) * 0.9), 6)
        exp_profit = round(((resistance - support) / support) * 100 * 0.4, 1)

        return {
            'symbol':     symbol,
            'price':      price,
            'score':      score,
            'rsi_15m':    rsi_15m,
            'rsi_1h':     rsi_1h,
            'rsi_4h':     rsi_4h,
            'ema20':      round(ema20, 6),
            'ema50':      round(ema50, 6),
            'grid_low':   support,
            'grid_high':  resistance,
            'liq_price':  liq_price,
            'exp_profit': exp_profit,
            'vol_spike':  is_spike,
            'spike_x':    spike_x,
            'rsi_exit':   rsi_1h > RSI_EXIT
        }

    except Exception as e:
        print(f"  ❌ {symbol}: {e}")
        return None

# ============================================================
# MESSAGES
# ============================================================

def entry_msg(d):
    risk     = "🟢 LOW" if d['score'] >= 80 else "🟡 MEDIUM" if d['score'] >= 60 else "🔴 HIGH"
    spike_txt = f"\n⚡ Volume Spike: {d['spike_x']}x !" if d['vol_spike'] else ""
    return f"""
🚨 <b>SIGNAL FOUND!</b>
━━━━━━━━━━━━━━━━━━━
💎 <b>{d['symbol']}</b>
💰 Price: ${d['price']}
⭐ Score: {d['score']}/100 | {risk}{spike_txt}

📊 <b>RSI:</b>
15m: {d['rsi_15m']} {'✅' if RSI_ENTRY_MIN <= d['rsi_15m'] <= RSI_ENTRY_MAX else '⚠️'}
1H:  {d['rsi_1h']}  {'✅' if RSI_ENTRY_MIN <= d['rsi_1h']  <= RSI_ENTRY_MAX else '⚠️'}
4H:  {d['rsi_4h']}  {'✅' if RSI_ENTRY_MIN <= d['rsi_4h']  <= RSI_ENTRY_MAX else '⚠️'}

📈 <b>EMA:</b>
EMA20: {d['ema20']} {'✅' if d['price'] > d['ema20'] else '❌'}
EMA50: {d['ema50']} {'✅' if d['ema20'] > d['ema50'] else '❌'}

⚙️ <b>Grid Bot Settings:</b>
━━━━━━━━━━━━━━━━━━━
Range:     ${d['grid_low']} — ${d['grid_high']}
Grids:     25
Leverage:  {LEVERAGE_SUGGESTION}x ⚠️
Expected:  ~{d['exp_profit']}%
Liq.Price: ~${d['liq_price']}

📱 Futures → Grid Bot → Long
🕐 {datetime.now().strftime('%H:%M:%S')}
━━━━━━━━━━━━━━━━━━━
⚠️ DYOR | Not Financial Advice"""

def exit_msg(d):
    return f"""
⚠️ <b>EXIT SIGNAL!</b>
━━━━━━━━━━━━━━━━━━━
💎 <b>{d['symbol']}</b>
🔴 RSI 1H: {d['rsi_1h']} (Overbought!)
🔴 RSI 4H: {d['rsi_4h']}
💰 <b>PROFIT LOCK KARO ABHI!</b>
🕐 {datetime.now().strftime('%H:%M:%S')}
━━━━━━━━━━━━━━━━━━━"""

def volume_spike_msg(d):
    return f"""
⚡ <b>VOLUME SPIKE!</b>
━━━━━━━━━━━━━━━━━━━
💎 <b>{d['symbol']}</b>
💰 Price: ${d['price']}
📊 Volume: {d['spike_x']}x average!
🔥 Big move possible!
🕐 {datetime.now().strftime('%H:%M:%S')}
━━━━━━━━━━━━━━━━━━━
👀 Watch this coin!"""

def summary_msg(total, signals, exits, spikes, btc_change):
    btc_emoji = "🟢" if btc_change > 0 else "🔴"
    return f"""
🔍 <b>Scan Complete</b>
━━━━━━━━━━━━━━━━━━━
📊 Coins Scanned: {total}
🚨 Entry Signals: {signals}
⚠️ Exit Signals:  {exits}
⚡ Volume Spikes: {spikes}
{btc_emoji} BTC Change: {btc_change:.2f}%
🕐 {datetime.now().strftime('%H:%M:%S')}
━━━━━━━━━━━━━━━━━━━
{'🎯 Check alerts above!' if signals > 0 else '⏳ Waiting for signals...'}"""

# ============================================================
# DAILY REPORT
# ============================================================

daily_signals   = []
daily_exits     = []
daily_spikes    = []

def send_daily_report():
    msg = f"""
📊 <b>DAILY REPORT</b>
━━━━━━━━━━━━━━━━━━━
📅 Date: {datetime.now().strftime('%Y-%m-%d')}

🚨 Entry Signals: {len(daily_signals)}
⚠️ Exit Signals:  {len(daily_exits)}
⚡ Volume Spikes: {len(daily_spikes)}

📈 <b>Top Signals Today:</b>"""

    if daily_signals:
        for s in daily_signals[-5:]:
            msg += f"\n• {s['symbol']} | Score: {s['score']}"
    else:
        msg += "\n• No signals today"

    msg += f"""

━━━━━━━━━━━━━━━━━━━
🤖 Bot running 24/7
⏰ Next scan: 15 min"""

    send_telegram(msg)
    # Reset daily counts
    daily_signals.clear()
    daily_exits.clear()
    daily_spikes.clear()
    print("📊 Daily report sent!")

# ============================================================
# MAIN SCAN
# ============================================================

alerted      = {}
exit_alerted = {}
spike_alerted = {}

def run_scan():
    print(f"\n{'='*50}")
    print(f"🔍 SCAN: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}")

    try:
        exchange = get_exchange()

        # BTC crash check pehle!
        print("🔍 Checking BTC...")
        btc_change, btc_price = check_btc_crash(exchange)
        print(f"  BTC: ${btc_price} | {btc_change:.2f}%")

        # Coins data lo
        coins = get_coins_data(exchange)
        if not coins:
            send_telegram("⚠️ No coins found!")
            return

        entry_signals  = []
        exit_signals   = []
        spike_signals  = []

        for i, coin in enumerate(coins):
            print(f"\n[{i+1}/{len(coins)}] {coin['symbol']}...")
            result = analyze_coin(
                exchange,
                coin['symbol'],
                coin['price'],
                coin['volume']
            )

            if result is None:
                continue

            # Entry signal
            if result['score'] >= 60:
                if time.time() - alerted.get(coin['symbol'], 0) > 3600:
                    entry_signals.append(result)
                    alerted[coin['symbol']] = time.time()
                    daily_signals.append(result)
                    print(f"  🚨 SIGNAL! Score:{result['score']}")

            # Exit signal
            if result['rsi_exit']:
                if time.time() - exit_alerted.get(coin['symbol'], 0) > 3600:
                    exit_signals.append(result)
                    exit_alerted[coin['symbol']] = time.time()
                    daily_exits.append(result)
                    print(f"  ⚠️ EXIT!")

            # Volume spike
            if result['vol_spike']:
                if time.time() - spike_alerted.get(coin['symbol'], 0) > 3600:
                    spike_signals.append(result)
                    spike_alerted[coin['symbol']] = time.time()
                    daily_spikes.append(result)
                    print(f"  ⚡ SPIKE! {result['spike_x']}x")

        # Sort by score
        entry_signals.sort(key=lambda x: x['score'], reverse=True)

        # Send top 3 entries
        sent = 0
        for s in entry_signals[:3]:
            send_telegram(entry_msg(s))
            sent += 1
            time.sleep(1)

        # Send exits
        for s in exit_signals[:2]:
            send_telegram(exit_msg(s))
            time.sleep(1)

        # Send volume spikes
        for s in spike_signals[:2]:
            if not any(x['symbol'] == s['symbol'] for x in entry_signals[:3]):
                send_telegram(volume_spike_msg(s))
                time.sleep(1)

        # Summary
        send_telegram(summary_msg(
            len(coins), sent,
            len(exit_signals),
            len(spike_signals),
            btc_change
        ))

        print(f"\n✅ DONE! Signals:{sent} Exits:{len(exit_signals)} Spikes:{len(spike_signals)}")

    except Exception as e:
        print(f"❌ ERROR: {e}")
        send_telegram(f"⚠️ Error: {str(e)[:100]}")

# ============================================================
# START
# ============================================================

def start_bot():
    print("🚀 CRYPTO ALERT BOT V3 STARTING...")
    print("="*50)
    print(f"📊 Coins: {len(TOP_COINS)}")
    print(f"⏰ Scan: Every {SCAN_INTERVAL_MINUTES} min")
    print(f"📈 RSI Entry: {RSI_ENTRY_MIN}-{RSI_ENTRY_MAX}")
    print(f"📉 RSI Exit: {RSI_EXIT}+")
    print(f"🚨 BTC Crash: {BTC_CRASH_THRESHOLD}%")
    print(f"⚡ Volume Spike: {VOLUME_SPIKE_MULTIPLIER}x")
    print("="*50)

    send_telegram(f"""
🤖 <b>Smart Crypto Alert Bot V3!</b>
━━━━━━━━━━━━━━━━━━━
✅ {len(TOP_COINS)} coins scanning
✅ RSI 15m + 1H + 4H
✅ EMA 20/50 analysis
✅ Volume spike detection
✅ BTC crash alerts
✅ Daily reports
⏰ Every {SCAN_INTERVAL_MINUTES} minutes
━━━━━━━━━━━━━━━━━━━
🚀 Starting now...
    """)

    # Pehla scan
    run_scan()

    # Schedule
    schedule.every(SCAN_INTERVAL_MINUTES).minutes.do(run_scan)

    # Daily report roz raat 10 baje
    schedule.every().day.at("22:00").do(send_daily_report)

    print(f"\n⏰ Next scan in {SCAN_INTERVAL_MINUTES} min...")
    print("Running... Ctrl+C to stop\n")

    while True:
        schedule.run_pending()
        time.sleep(30)

if __name__ == "__main__":
    start_bot()
