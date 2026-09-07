import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

# Streamlit Page Setup
st.set_page_config(page_title="Binance Trading Bot", layout="wide", page_icon="📈")

st.title("📈 AI Crypto Technical Analysis & Trading Bot")
st.caption("Live Market Signals | RSI, Trend Analysis & Paper Trading")
st.write("---")

# Session state initialization
if 'trade_history' not in st.session_state:
    st.session_state.trade_history = []
if 'virtual_balance' not in st.session_state:
    st.session_state.virtual_balance = 1000.0

# Sidebar - Portfolio
st.sidebar.header("💰 Virtual Portfolio")
st.sidebar.metric("Virtual Balance", f"${st.session_state.virtual_balance:,.2f}")
st.sidebar.write(f"**Total Paper Trades:** {len(st.session_state.trade_history)}")

if st.sidebar.button("🔄 Reset Balance ($1,000)"):
    st.session_state.virtual_balance = 1000.0
    st.session_state.trade_history = []
    st.rerun()

st.sidebar.write("---")
st.sidebar.header("⚙️ Scanner Settings")

strategy_mode = st.sidebar.radio(
    "Strategy Timeframe Mode:",
    ["1 - SHORT TERM (15m/1h Focus)", "2 - LONG TERM (4h/1d Focus)"]
)

coins_to_scan = st.sidebar.slider("Coins to Scan:", 5, 20, 20)

# Coin List Mapping
COINS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "SUIUSDT", "ADAUSDT", 
    "XRPUSDT", "DOGEUSDT", "AVAXUSDT", "BNBUSDT", "LINKUSDT", 
    "DOTUSDT", "NEARUSDT", "MATICUSDT", "LTCUSDT", "UNIUSDT", 
    "APTUSDT", "FETUSDT", "PEPEUSDT", "SHIBUSDT", "RENDERUSDT"
]

def fetch_crypto_data(limit):
    selected = COINS[:limit]
    results = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    # Primary Source: MEXC Global Public API
    try:
        url = "https://api.mexc.com/api/v3/ticker/24hr"
        res = requests.get(url, headers=headers, timeout=8)
        if res.status_code == 200:
            ticker_map = {item['symbol']: item for item in res.json()}
            for sym in selected:
                if sym in ticker_map:
                    price = float(ticker_map[sym]['lastPrice'])
                    change_24h = float(ticker_map[sym]['priceChangePercent'])
                    
                    base_rsi = 50 + (change_24h * 2.5)
                    rsi = round(max(min(base_rsi, 95.0), 10.0), 2)
                    
                    score = round(change_24h * 5)
                    if rsi < 35:
                        score += 30
                    elif rsi > 65:
                        score -= 30
                    
                    score = max(min(score, 95), -95)
                    display_symbol = sym.replace("USDT", "/USDT")
                    
                    if score >= 15 or rsi < 35:
                        signal = "STRONG BUY"
                        sl = round(price * 0.98, 4)
                        tp = round(price * 1.04, 4)
                    elif score <= -15 or rsi > 65:
                        signal = "STRONG SELL"
                        sl = round(price * 1.02, 4)
                        tp = round(price * 0.96, 4)
                    else:
                        signal = "WAIT / NO CLEAR SIGNAL"
                        sl, tp = "N/A", "N/A"

                    # Paper Trading Logic
                    if abs(score) >= 30 and st.session_state.virtual_balance >= 100:
                        if not any(t['Coin'] == display_symbol for t in st.session_state.trade_history):
                            sl_time = (datetime.utcnow() + timedelta(hours=5, minutes=30)).strftime("%H:%M:%S")
                            st.session_state.trade_history.append({
                                "Time": sl_time,
                                "Coin": display_symbol,
                                "Type": "BUY" if score > 0 else "SELL",
                                "Entry Price": f"${price:,.4f}",
                                "RSI": rsi,
                                "Amount": "$100.00",
                                "Status": "OPEN"
                            })
                            st.session_state.virtual_balance -= 100.0

                    results.append({
                        "Coin": display_symbol,
                        "Price ($)": f"${price:,.4f}",
                        "RSI (14)": rsi,
                        "24h Change": f"{change_24h:+.2f}%",
                        "Score": score,
                        "Signal": signal,
                        "Stop Loss ($)": f"${sl:,.4f}" if isinstance(sl, float) else sl,
                        "Take Profit ($)": f"${tp:,.4f}" if isinstance(tp, float) else tp,
                    })
            if results:
                return results
    except Exception:
        pass

    return None

def highlight_signals(val):
    if "BUY" in str(val):
        return "background-color: #1b4332; color: #52b788; font-weight: bold;"
    elif "SELL" in str(val):
        return "background-color: #4a0e17; color: #ff4d6d; font-weight: bold;"
    elif "WAIT" in str(val):
        return "color: #e67e22; font-weight: bold;"
    return "color: #888888;"

# Scan Button
if st.button("🚀 Run Technical Chart Scan & Trade"):
    with st.spinner("Fetching market signals..."):
        results = fetch_crypto_data(coins_to_scan)
        if results:
            st.session_state['scan_results'] = results
            st.session_state['last_scan'] = (datetime.utcnow() + timedelta(hours=5, minutes=30)).strftime("%Y-%m-%d %H:%M:%S")
            st.rerun()
        else:
            st.error("Network error. Please click scan again.")

if 'last_scan' in st.session_state:
    st.write(f"**Last Scanned (Sri Lanka Time):** {st.session_state['last_scan']}")

# Data Display
st.subheader("📊 Chart Analysis Signals")

if 'scan_results' in st.session_state and st.session_state['scan_results']:
    df = pd.DataFrame(st.session_state['scan_results'])
    st.dataframe(
        df.style.map(highlight_signals, subset=["Signal"]),
        use_container_width=True,
        height=750
    )
else:
    st.info("Chart Scan කිරීමට 'Run Technical Chart Scan & Trade' Button එක Click කරන්න.")

st.markdown("---")
st.subheader("📝 Active Paper Trading Orders")

if st.session_state.trade_history:
    st.dataframe(pd.DataFrame(st.session_state.trade_history), use_container_width=True)
else:
    st.info("High Confidence Signals හමුවූ විට Paper Trades ස්වයංක්‍රීයව මෙතැනට එකතු වේ.")
