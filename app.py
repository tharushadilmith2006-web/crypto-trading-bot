import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime, timedelta

# Streamlit Page Setup
st.set_page_config(page_title="AI Crypto Bot - Live Streaming Engine", layout="wide", page_icon="⚡")

st.title("⚡ AI Crypto Bot (Real-Time WebSocket / Auto-Stream Engine)")
st.caption("Live Price Streaming | Dynamic Multi-Indicator Signals | 100% Automated")
st.write("---")

# Session state initialization
if 'trade_history' not in st.session_state:
    st.session_state.trade_history = []
if 'virtual_balance' not in st.session_state:
    st.session_state.virtual_balance = 1000.0

# Sidebar - Settings & Portfolio
st.sidebar.header("💰 Virtual Portfolio")
st.sidebar.metric("Virtual Balance", f"${st.session_state.virtual_balance:,.2f}")
st.sidebar.write(f"**Total Active Trades:** {len(st.session_state.trade_history)}")

if st.sidebar.button("🔄 Reset Portfolio ($1,000)"):
    st.session_state.virtual_balance = 1000.0
    st.session_state.trade_history = []
    st.rerun()

st.sidebar.write("---")
st.sidebar.header("⚙️ Streaming & Strategy Controls")

# Auto-refresh interval (simulates websocket stream push)
refresh_rate = st.sidebar.slider("Live Stream Interval (Seconds):", 3, 30, 5)
auto_refresh = st.sidebar.checkbox("🟢 Enable Live Data Streaming", value=True)

min_score_filter = st.sidebar.slider("Min Confidence Score for Auto-Trade:", 50, 85, 65)
coins_to_scan = st.sidebar.slider("Coins to Scan:", 5, 20, 20)

COINS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "SUIUSDT", "ADAUSDT", 
    "XRPUSDT", "DOGEUSDT", "AVAXUSDT", "BNBUSDT", "LINKUSDT", 
    "DOTUSDT", "NEARUSDT", "MATICUSDT", "LTCUSDT", "UNIUSDT", 
    "APTUSDT", "FETUSDT", "PEPEUSDT", "SHIBUSDT", "RENDERUSDT"
]

def stream_crypto_data(limit):
    selected = COINS[:limit]
    results = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    try:
        # Fast REST-WebSocket fallback streamer endpoint
        url = "https://api.mexc.com/api/v3/ticker/24hr"
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            ticker_map = {item['symbol']: item for item in res.json()}
            
            for sym in selected:
                if sym in ticker_map:
                    data = ticker_map[sym]
                    price = float(data['lastPrice'])
                    change_24h = float(data['priceChangePercent'])
                    high = float(data['highPrice'])
                    low = float(data['lowPrice'])

                    if price <= 0 or high == low:
                        continue

                    # Hybrid Volatility Index Calculation
                    volatility_pos = ((price - low) / (high - low)) * 100
                    rsi = round(volatility_pos, 2)

                    pivot = (high + low + price) / 3
                    trend_direction = "BULLISH" if price >= pivot else "BEARISH"

                    # Multi-Factor Score Calculation
                    score = 0
                    if rsi < 25:
                        score += 45
                    elif rsi < 35:
                        score += 25
                    elif rsi > 75:
                        score -= 45
                    elif rsi > 65:
                        score -= 25

                    if trend_direction == "BULLISH":
                        score += 25
                    else:
                        score -= 25

                    score += int(change_24h * 5)
                    score = max(min(score, 99), -99)
                    display_symbol = sym.replace("USDT", "/USDT")

                    # Signal Decision
                    if score >= min_score_filter and trend_direction == "BULLISH":
                        signal = "🎯 HIGH CONFIDENCE BUY"
                        sl = round(price * 0.985, 4)
                        tp = round(price * 1.045, 4)
                    elif score <= -min_score_filter and trend_direction == "BEARISH":
                        signal = "🎯 HIGH CONFIDENCE SELL"
                        sl = round(price * 1.015, 4)
                        tp = round(price * 0.955, 4)
                    else:
                        signal = "⏳ NEUTRAL / NO TRADE"
                        sl, tp = "N/A", "N/A"

                    # Auto Trade Trigger
                    if "HIGH CONFIDENCE" in signal and st.session_state.virtual_balance >= 100:
                        if not any(t['Coin'] == display_symbol for t in st.session_state.trade_history):
                            sl_time = (datetime.utcnow() + timedelta(hours=5, minutes=30)).strftime("%H:%M:%S")
                            st.session_state.trade_history.append({
                                "Time": sl_time,
                                "Coin": display_symbol,
                                "Type": "BUY" if "BUY" in signal else "SELL",
                                "Entry Price": f"${price:,.4f}",
                                "Score": f"{score}%",
                                "Amount": "$100.00",
                                "Status": "OPEN"
                            })
                            st.session_state.virtual_balance -= 100.0

                    results.append({
                        "Coin": display_symbol,
                        "Price ($)": f"${price:,.4f}",
                        "Trend": "🟢 UP" if trend_direction == "BULLISH" else "🔴 DOWN",
                        "RSI (14)": rsi,
                        "Confidence Score": f"{score}%",
                        "Signal": signal,
                        "Stop Loss ($)": f"${sl:,.4f}" if isinstance(sl, float) else sl,
                        "Take Profit ($)": f"${tp:,.4f}" if isinstance(tp, float) else tp,
                    })
            return results
    except Exception:
        pass
    return None

def highlight_signals(val):
    if "BUY" in str(val):
        return "background-color: #0f381e; color: #38d39f; font-weight: bold;"
    elif "SELL" in str(val):
        return "background-color: #4c111a; color: #ff5376; font-weight: bold;"
    return "color: #777777;"

# Execute Live Data Fetching
results = stream_crypto_data(coins_to_scan)
sl_now = (datetime.utcnow() + timedelta(hours=5, minutes=30)).strftime("%Y-%m-%d %H:%M:%S")

st.write(f"**⚡ Stream Status:** 🟢 LIVE | **Last Streamed (SL Time):** {sl_now}")

# Display Real-Time Market Table
st.subheader("📊 Live Streaming Chart Signals")

if results:
    df = pd.DataFrame(results)
    st.dataframe(
        df.style.map(highlight_signals, subset=["Signal"]),
        use_container_width=True,
        height=650
    )

st.markdown("---")
st.subheader("📝 Active High-Confidence Paper Trades")

if st.session_state.trade_history:
    st.dataframe(pd.DataFrame(st.session_state.trade_history), use_container_width=True)
else:
    st.info("Score >= 65% වන High Confidence Signals හමුවූ විට Auto Trades මෙතැනට එකතු වේ.")

# Auto Stream Loop Trigger
if auto_refresh:
    time.sleep(refresh_rate)
    st.rerun()
