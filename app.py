import time
from datetime import datetime
import pandas as pd
import streamlit as st

# main.py එකෙන් Functions Import කරගැනීම
from main import get_top_binance_coins, scan_symbol

# Streamlit Page Setup
st.set_page_config(
    page_title="Crypto Bot & Paper Trading Engine", page_icon="📈", layout="wide"
)

st.title("🤖 AI Crypto Trading Bot - Paper Trading Engine")
st.caption(
    "Virtual Trading Wallet | Strategy Testing | Dynamic Risk Management (1:2 R:R)"
)

# ----------------------------------------------------
# 1. PAPER TRADING SESSION STATE (Virtual Wallet Setup)
# ----------------------------------------------------
if "virtual_balance" not in st.session_state:
    st.session_state.virtual_balance = (
        1000.0  # ஆரம்ப Virtual Balance එක $1,000 යි
    )

if "trade_history" not in st.session_state:
    st.session_state.trade_history = []

# ----------------------------------------------------
# 2. SIDEBAR - VIRTUAL PORTFOLIO CONTROLS
# ----------------------------------------------------
st.sidebar.header("💰 Virtual Portfolio")
st.sidebar.metric(
    "Virtual Balance", f"${st.session_state.virtual_balance:,.2f}"
)

# Total Trades count
total_trades = len(st.session_state.trade_history)
st.sidebar.write(f"**Total Paper Trades:** {total_trades}")

if st.sidebar.button("🔄 Reset Balance ($1,000)"):
    st.session_state.virtual_balance = 1000.0
    st.session_state.trade_history = []
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.header("⚙️ Scanner Settings")
mode = st.sidebar.radio(
    "Strategy Mode:",
    ["1 - SHORT TERM (15m/1h Focus)", "2 - LONG TERM (4h/1d Focus)"],
)
coin_limit = st.sidebar.slider("Coins to Scan:", 5, 20, 10)

# ----------------------------------------------------
# 3. MARKET SCANNER & AUTO PAPER TRADER
# ----------------------------------------------------
def run_scanner_and_paper_trade():
    coins = get_top_binance_coins(limit=coin_limit)
    results = []

    progress_bar = st.progress(0)
    status_text = st.empty()

    for idx, coin in enumerate(coins):
        status_text.text(f"Scanning {coin} ({idx + 1}/{len(coins)})...")
        price, score, signal, sl, tp = scan_symbol(coin, mode[0])

        # Paper Trading Simulation Logic ($50 per position)
        if signal in ["LONG 🟢", "SHORT 🔴"]:
            trade_amount = 50.0  # Trade එකකට යොදවන සතය $50 යි
            if st.session_state.virtual_balance >= trade_amount:
                # Check if trade already executed for this coin
                existing = [
                    t
                    for t in st.session_state.trade_history
                    if t["Coin"] == coin and t["Status"] == "OPEN"
                ]
                if not existing:
                    st.session_state.trade_history.append(
                        {
                            "Time": datetime.now().strftime("%H:%M:%S"),
                            "Coin": coin,
                            "Type": signal,
                            "Entry Price": f"${price:,.4f}",
                            "Stop Loss": f"${sl:,.4f}",
                            "Take Profit": f"${tp:,.4f}",
                            "Invested": f"${trade_amount}",
                            "Status": "OPEN",
                        }
                    )

        results.append(
            {
                "Coin": coin,
                "Price ($)": f"${price:,.4f}",
                "Score": score,
                "Signal": signal,
                "Stop Loss ($)": f"${sl:,.4f}" if sl > 0 else "N/A",
                "Take Profit ($)": f"${tp:,.4f}" if tp > 0 else "N/A",
                "R:R Ratio": "1:2" if sl > 0 else "N/A",
            }
        )
        progress_bar.progress((idx + 1) / len(coins))
        time.sleep(0.1)

    status_text.empty()
    progress_bar.empty()
    return pd.DataFrame(results)


# UI Action Button
if st.button("🚀 Start Market Scan & Paper Trade"):
    st.write(f"**Last Scanned:** {datetime.now().strftime('%H:%M:%S')}")
    df_results = run_scanner_and_paper_trade()

    def highlight_signals(val):
        if "LONG" in str(val):
            return "background-color: #1b5e20; color: white; font-weight: bold;"
        elif "SHORT" in str(val):
            return "background-color: #b71c1c; color: white; font-weight: bold;"
        return "color: #888888;"

    st.subheader("📊 Live Market Signals")
    st.dataframe(
        df_results.style.map(highlight_signals, subset=["Signal"]),
        use_container_width=True,
    )

# ----------------------------------------------------
# 4. PAPER TRADING HISTORY TABLE
# ----------------------------------------------------
st.markdown("---")
st.subheader("📝 Active Paper Trading Orders")

if st.session_state.trade_history:
    df_trades = pd.DataFrame(st.session_state.trade_history)
    st.dataframe(df_trades, use_container_width=True)
else:
    st.info(
        "තවම Paper Trades සටහන් වී නැත. 'Start Market Scan & Paper Trade' එක Click කරන්න."
    )
