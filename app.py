import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

# Streamlit Page Setup
st.set_page_config(page_title="Binance Trading Bot", layout="wide", page_icon="📈")

st.title("📈 AI Crypto Technical Analysis & Trading Bot")
st.caption("RSI, EMA 20/50 & Trend Analysis | Dynamic Timeframes (15m/1h & 4h/1d)")
st.write("---")

# Session state initialization
if 'trade_history' not in st.session_state:
    st.session_state.trade_history = []
if 'virtual_balance' not in st.session_state:
    st.session_state.virtual_balance = 1000.0

# Sidebar - Settings
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
    ("bitcoin", "BTC/USDT"), ("ethereum", "ETH/USDT"), ("solana", "SOL/USDT"),
    ("sui", "SUI/USDT"), ("cardano", "ADA/USDT"), ("ripple", "XRP/USDT"),
    ("dogecoin", "DOGE/USDT"), ("avalanche-2", "AVAX/USDT"), ("binancecoin", "BNB/USDT"),
    ("chainlink", "LINK/USDT"), ("polkadot", "DOT/USDT"), ("near", "NEAR/USDT"),
    ("polygon-ecosystem-token", "MATIC/USDT"), ("litecoin", "LTC/USDT"), ("uniswap", "UNI/USDT"),
    ("aptos", "APT/USDT"), ("artificial-superintelligence-alliance", "FET/USDT"),
    ("pepe", "PEPE/USDT"), ("shiba-inu", "SHIB/USDT"), ("render-token", "RENDER/USDT")
]

def analyze_crypto(coin_id, symbol, mode):
    """Fetch OHLCV historical data and calculate RSI & EMA crossover"""
    days = "1" if "SHORT" in mode else "30"
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days={days}"
    
    try:
        res = requests.get(url, timeout=10)
        if res.status_code != 200:
            return None
        
        prices = [p[1] for p in res.json().get('prices', [])]
        if len(prices) < 30:
            return None
            
        df = pd.DataFrame({'price': prices})
        
        # Calculate EMA 20 & EMA 50
        df['ema_20'] = df['price'].ewm(span=20, adjust=False).mean()
        df['ema_50'] = df['price'].ewm(span=50, adjust=False).mean()
        
        # Calculate RSI (14 period)
        delta = df['price'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        latest_price = df['price'].iloc[-1]
        latest_rsi = round(df['rsi'].iloc[-1], 2)
        latest_ema20 = df['ema_20'].iloc[-1]
        latest_ema50 = df['ema_50'].iloc[-1]
        
        # Scoring Logic based on Technical Indicators
        score = 0
        
        # RSI Analysis
        if latest_rsi < 35:
            score += 40  # Oversold (Strong Buy Signal)
        elif latest_rsi > 65:
            score -= 40  # Overbought (Strong Sell Signal)
            
        # EMA Trend Crossover Analysis
        if latest_ema20 > latest_ema50:
            score += 45  # Bullish Trend
        else:
            score -= 45  # Bearish Trend
            
        # Final Signal Determination
        if score >= 50:
            signal = "STRONG BUY"
            sl = round(latest_price * 0.98, 4)
            tp = round(latest_price * 1.04, 4)
        elif score <= -50:
            signal = "STRONG SELL"
            sl = round(latest_price * 1.02, 4)
            tp = round(latest_price * 0.96, 4)
        else:
            signal = "WAIT / NO CLEAR SIGNAL"
            sl, tp = "N/A", "N/A"
            
        # Execute Paper Trade for High Scoring Signals
        if abs(score) >= 70 and st.session_state.virtual_balance >= 100:
            if not any(t['Coin'] == symbol for t in st.session_state.trade_history):
                sl_time = (datetime.utcnow() + timedelta(hours=5, minutes=30)).strftime("%H:%M:%S")
                st.session_state.trade_history.append({
                    "Time": sl_time,
                    "Coin": symbol,
                    "Type": "BUY" if score > 0 else "SELL",
                    "Entry Price": f"${latest_price:,.4f}",
                    "RSI": latest_rsi,
                    "Amount": "$100.00",
                    "Status": "OPEN"
                })
                st.session_state.virtual_balance -= 100.0

        return {
            "Coin": symbol,
            "Price ($)": f"${latest_price:,.4f}",
            "RSI (14)": latest_rsi,
            "EMA Trend": "BULLISH 🟢" if latest_ema20 > latest_ema50 else "BEARISH 🔴",
            "Score": score,
            "Signal": signal,
            "Stop Loss ($)": f"${sl:,.4f}" if isinstance(sl, float) else sl,
            "Take Profit ($)": f"${tp:,.4f}" if isinstance(tp, float) else tp,
        }
    except Exception:
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
    results = []
    progress_bar = st.progress(0)
    selected_coins = COINS[:coins_to_scan]
    
    for idx, (c_id, sym) in enumerate(selected_coins):
        res = analyze_crypto(c_id, sym, strategy_mode)
        if res:
            results.append(res)
        progress_bar.progress((idx + 1) / len(selected_coins))
        
    progress_bar.empty()
    st.session_state['scan_results'] = results
    st.session_state['last_scan'] = (datetime.utcnow() + timedelta(hours=5, minutes=30)).strftime("%Y-%m-%d %H:%M:%S")
    st.rerun()

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
