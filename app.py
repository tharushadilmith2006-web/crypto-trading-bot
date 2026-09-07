import streamlit as st
import pandas as pd
import ccxt
import time
from datetime import datetime

# Initialize binance exchange
binance = ccxt.binance({
    'enableRateLimit': True,
})

# App configs
st.set_page_config(page_title="Crypto Bot & Paper Trading Engine", layout="wide", page_icon="📈")

# --- UI Layout ---
st.title("📈 Crypto Bot & Paper Trading Engine")
st.caption("Virtual Trading Wallet | Strategy Testing | Dynamic Risk Management (1:2 R:R)")
st.write("---")

# Session state initialization
if 'trade_history' not in st.session_state:
    st.session_state.trade_history = []
if 'virtual_balance' not in st.session_state:
    st.session_state.virtual_balance = 1000.0

# Sidebar - Virtual Portfolio
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
    "Strategy Mode:",
    ["1 - SHORT TERM (15m/1h Focus)", "2 - LONG TERM (4h/1d Focus)"]
)

coins_to_scan = st.sidebar.slider("Coins to Scan:", 5, 50, 20)

# Helper function to scan symbol safely with retry logic
def scan_symbol_safe(symbol):
    for attempt in range(3):
        try:
            ticker = binance.fetch_ticker(symbol)
            klines = binance.fetch_ohlcv(symbol, timeframe='1h', limit=20)
            
            if not ticker or not klines or len(klines) < 10:
                time.sleep(0.2)
                continue
                
            price = ticker.get('last', 0.0)
            closes = [k[4] for k in klines]
            ma = sum(closes) / len(closes)
            
            score = 0
            if price > ma:
                signal = "BUY / LONG"
                score = 80
                sl = round(price * 0.98, 4)
                tp = round(price * 1.04, 4)
                rr = "1:2.0"
            else:
                signal = "SELL / SHORT"
                score = -75
                sl = round(price * 1.02, 4)
                tp = round(price * 0.96, 4)
                rr = "1:2.0"
                
            return {
                "Coin": symbol.replace("/USDT", "USDT"),
                "Price ($)": f"${price:.4f}",
                "Score": score,
                "Signal": signal,
                "Stop Loss ($)": f"${sl:.4f}",
                "Take Profit ($)": f"${tp:.4f}",
                "R:R Ratio": rr
            }
        except Exception:
            time.sleep(0.3)
            
    return {
        "Coin": symbol.replace("/USDT", "USDT"),
        "Price ($)": "$0.0000",
        "Score": 0,
        "Signal": "DATA ERROR",
        "Stop Loss ($)": "N/A",
        "Take Profit ($)": "N/A",
        "R:R Ratio": "N/A"
    }

# Function to style signals
def highlight_signals(val):
    if "BUY" in str(val):
        return "background-color: #1b4332; color: #52b788; font-weight: bold;"
    elif "SHORT" in str(val) or "SELL" in str(val):
        return "background-color: #4a0e17; color: #ff4d6d; font-weight: bold;"
    return "color: #888888;"

# Main Action Button
if st.button("🚀 Start Market Scan & Paper Trade"):
    with st.spinner("Scanning market & updating signals..."):
        symbols = [
            'BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'SUI/USDT', 'ADA/USDT',
            'XRP/USDT', 'DOGE/USDT', 'AVAX/USDT', 'BNB/USDT', 'LINK/USDT',
            'DOT/USDT', 'NEAR/USDT', 'MATIC/USDT', 'LTC/USDT', 'UNI/USDT',
            'APT/USDT', 'FET/USDT', 'PEPE/USDT', 'SHIB/USDT', 'RENDER/USDT'
        ][:coins_to_scan]
        
        results = []
        progress_bar = st.progress(0)
        
        for idx, sym in enumerate(symbols):
            res = scan_symbol_safe(sym)
            results.append(res)
            progress_bar.progress((idx + 1) / len(symbols))
            
        progress_bar.empty()
        st.session_state['scan_results'] = results
        st.session_state['last_scan'] = datetime.now().strftime("%H:%M:%S")

# Display Last Scanned Time
if 'last_scan' in st.session_state:
    st.write(f"**Last Scanned:** {st.session_state['last_scan']}")

# Display Data Table
st.subheader("📊 Live Market Signals")

if 'scan_results' in st.session_state and st.session_state['scan_results']:
    df_results = pd.DataFrame(st.session_state['scan_results'])
    st.dataframe(
        df_results.style.map(highlight_signals, subset=["Signal"]),
        use_container_width=True,
        height=750  # Height 750 ලෙස යෙදූ බැවින් Coins 20ම පහළට එකපාර පෙනේ
    )
else:
    st.info("තවම Market Scan එකක් සිදු කර නැත. 'Start Market Scan & Paper Trade' එක Click කරන්න.")

# Paper Trading Section
st.markdown("---")
st.subheader("📝 Active Paper Trading Orders")

if st.session_state.trade_history:
    df_trades = pd.DataFrame(st.session_state.trade_history)
    st.dataframe(df_trades, use_container_width=True)
else:
    st.info("නැවුම් Paper Trades සටහන් වී නැත. 'Start Market Scan & Paper Trade' එක Click කරන්න.")
