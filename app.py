import streamlit as st
import pandas as pd
import requests
from datetime import datetime

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

coins_to_scan = st.sidebar.slider("Coins to Scan:", 5, 20, 20)

# Coin Mapping for CoinGecko API
COIN_MAPPING = {
    "BTCUSDT": ("bitcoin", "BTC/USDT"),
    "ETHUSDT": ("ethereum", "ETH/USDT"),
    "SOLUSDT": ("solana", "SOL/USDT"),
    "SUIUSDT": ("sui", "SUI/USDT"),
    "ADAUSDT": ("cardano", "ADA/USDT"),
    "XRPUSDT": ("ripple", "XRP/USDT"),
    "DOGEUSDT": ("dogecoin", "DOGE/USDT"),
    "AVAXUSDT": ("avalanche-2", "AVAX/USDT"),
    "BNBUSDT": ("binancecoin", "BNB/USDT"),
    "LINKUSDT": ("chainlink", "LINK/USDT"),
    "DOTUSDT": ("polkadot", "DOT/USDT"),
    "NEARUSDT": ("near", "NEAR/USDT"),
    "MATICUSDT": ("polygon-ecosystem-token", "MATIC/USDT"),
    "LTCUSDT": ("litecoin", "LTC/USDT"),
    "UNIUSDT": ("uniswap", "UNI/USDT"),
    "APTUSDT": ("aptos", "APT/USDT"),
    "FETUSDT": ("artificial-superintelligence-alliance", "FET/USDT"),
    "PEPEUSDT": ("pepe", "PEPE/USDT"),
    "SHIBUSDT": ("shiba-inu", "SHIB/USDT"),
    "RENDERUSDT": ("render-token", "RENDER/USDT")
}

def fetch_coingecko_data():
    """Fetches stable price and 24h change data from CoinGecko API"""
    selected_keys = list(COIN_MAPPING.keys())[:coins_to_scan]
    gecko_ids = [COIN_MAPPING[k][0] for k in selected_keys]
    
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={','.join(gecko_ids)}&vs_currencies=usd&include_24hr_change=true"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            results = []
            
            for key in selected_keys:
                g_id, display_symbol = COIN_MAPPING[key]
                coin_data = data.get(g_id, {})
                price = coin_data.get('usd', 0.0)
                change = coin_data.get('usd_24h_change', 0.0)
                
                # Signal Generation Logic based on 24h Trend
                if change > 0:
                    signal = "BUY / LONG"
                    score = min(round(50 + change * 5), 95)
                    sl = round(price * 0.98, 4)
                    tp = round(price * 1.04, 4)
                else:
                    signal = "SELL / SHORT"
                    score = max(round(-50 + change * 5), -95)
                    sl = round(price * 1.02, 4)
                    tp = round(price * 0.96, 4)
                
                results.append({
                    "Coin": display_symbol,
                    "Price ($)": f"${price:,.4f}",
                    "Score": score,
                    "Signal": signal,
                    "Stop Loss ($)": f"${sl:,.4f}",
                    "Take Profit ($)": f"${tp:,.4f}",
                    "R:R Ratio": "1:2.0"
                })
            return results
    except Exception:
        pass
    return None

# Function to style signals
def highlight_signals(val):
    if "BUY" in str(val):
        return "background-color: #1b4332; color: #52b788; font-weight: bold;"
    elif "SHORT" in str(val) or "SELL" in str(val):
        return "background-color: #4a0e17; color: #ff4d6d; font-weight: bold;"
    return "color: #888888;"

# Main Action Button
if st.button("🚀 Start Market Scan & Paper Trade"):
    with st.spinner("Fetching market data & calculating signals..."):
        results = fetch_coingecko_data()
        if results:
            st.session_state['scan_results'] = results
            st.session_state['last_scan'] = datetime.now().strftime("%H:%M:%S")
        else:
            st.error("API Fetch Error! Please try clicking scan again.")

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
