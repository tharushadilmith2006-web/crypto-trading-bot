import json
import time
import urllib.request

# ====================================================
# STEP 1: DATA FETCHING ENGINE
# ====================================================

def get_top_binance_coins(limit=10):
    """Binance එකේ Volume එක වැඩිම Top USDT Pairs Auto-Fetch කරයි."""
    try:
        url = "https://api.binance.com/api/v3/ticker/24hr"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        response = urllib.request.urlopen(req).read()
        data = json.loads(response)

        usdt_pairs = [
            item for item in data
            if item["symbol"].endswith("USDT")
            and not any(x in item["symbol"] for x in ["UPUSDT", "DOWNUSDT", "BUSD", "USDC"])
        ]
        sorted_pairs = sorted(usdt_pairs, key=lambda x: float(x["quoteVolume"]), reverse=True)
        return [item["symbol"] for item in sorted_pairs[:limit]]
    except Exception as e:
        print(f"Error fetching symbols: {e}")
        return ["BTCUSDT", "ETHUSDT", "SOLUSDT", "SUIUSDT", "ADAUSDT"]

def fetch_klines(symbol, interval="1h", limit=100):
    """Binance API එකෙන් Price Data ලබාගනියි."""
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        response = urllib.request.urlopen(req).read()
        return json.loads(response)
    except Exception as e:
        print(f"Error fetching klines for {symbol}: {e}")
        return None

# ====================================================
# STEP 2 & 3: INDICATORS & CHART STRUCTURE
# ====================================================

def calculate_ema(prices, period):
    if len(prices) < period:
        return prices[-1]
    sma = sum(prices[:period]) / period
    multiplier = 2 / (period + 1)
    ema = sma
    for price in prices[period:]:
        ema = (price - ema) * multiplier + ema
    return ema

def calculate_rsi(prices, period=14):
    if len(prices) < period + 1:
        return 50.0

    gains, losses = [], []
    for i in range(1, len(prices)):
        change = prices[i] - prices[i - 1]
        gains.append(max(change, 0))
        losses.append(max(-change, 0))

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period

    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def calculate_atr(candles, period=14):
    """Average True Range (Volatility Calculation for SL/TP)."""
    if not candles or len(candles) < period + 1:
        return 0.0

    tr_list = []
    for i in range(1, len(candles)):
        high = float(candles[i][2])
        low = float(candles[i][3])
        prev_close = float(candles[i - 1][4])

        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        tr_list.append(tr)

    return sum(tr_list[-period:]) / period

def analyze_chart_structure(candles):
    if not candles or len(candles) < 30:
        return {"support": 0, "resistance": 0, "pattern": "NEUTRAL", "pattern_score": 0}

    highs = [float(c[2]) for c in candles]
    lows = [float(c[3]) for c in candles]
    closes = [float(c[4]) for c in candles]

    resistance = max(highs[-30:])
    support = min(lows[-30:])
    current_price = closes[-1]

    pattern = "NO_PATTERN"
    pattern_score = 0

    h1, h2 = max(highs[-20:-10]), max(highs[-10:])
    l1, l2 = min(lows[-20:-10]), min(lows[-10:])

    if h2 > h1 and l2 > l1:
        pattern = "UPTREND (HH/HL)"
        pattern_score += 2
    elif h2 < h1 and l2 < l1:
        pattern = "DOWNTREND (LH/LL)"
        pattern_score -= 2

    return {
        "support": support,
        "resistance": resistance,
        "pattern": pattern,
        "pattern_score": pattern_score
    }

# ====================================================
# STEP 4: RISK MANAGEMENT & TARGET CALCULATOR
# ====================================================

def calculate_risk_targets(signal_type, current_price, atr, support, resistance):
    """
    ATR & Structure මත පදනම් වූ Dynamic Stop-Loss & Take-Profit (Risk-Reward 1:2).
    """
    if "LONG" in signal_type:
        # Stop Loss = ATR buffer එකක් සහිතව Support එකට තරමක් පහලින්
        sl_distance = max(atr * 1.5, current_price * 0.015)  # Min 1.5% SL
        stop_loss = current_price - sl_distance
        
        # Risk to Reward 1:2 Ratio
        risk = current_price - stop_loss
        take_profit = current_price + (risk * 2.0)
        return round(stop_loss, 4), round(take_profit, 4)

    elif "SHORT" in signal_type:
        sl_distance = max(atr * 1.5, current_price * 0.015)
        stop_loss = current_price + sl_distance
        
        risk = stop_loss - current_price
        take_profit = current_price - (risk * 2.0)
        return round(stop_loss, 4), round(take_profit, 4)

    return 0.0, 0.0

# ====================================================
# MULTI-TIMEFRAME ENGINE
# ====================================================

def scan_symbol(symbol, mode_choice):
    candles_1h = fetch_klines(symbol, interval="1h", limit=100)
    if not candles_1h:
        return 0, 0, "ERROR", 0, 0

    prices = [float(c[4]) for c in candles_1h]
    current_price = prices[-1]

    ema20 = calculate_ema(prices, 20)
    ema50 = calculate_ema(prices, 50)
    rsi = calculate_rsi(prices, 14)
    atr = calculate_atr(candles_1h, 14)

    chart_info = analyze_chart_structure(candles_1h)

    score = 0
    if current_price > ema20 and ema20 > ema50:
        score += 3
    elif current_price < ema20 and ema20 < ema50:
        score -= 3

    if 55 < rsi < 70:
        score += 2
    elif 30 < rsi < 45:
        score -= 2

    score += chart_info["pattern_score"]

    if score >= 6:
        signal = "LONG 🟢"
    elif score <= -6:
        signal = "SHORT 🔴"
    else:
        signal = "WAIT ⚪"

    stop_loss, take_profit = calculate_risk_targets(
        signal, current_price, atr, chart_info["support"], chart_info["resistance"]
    )

    return current_price, score, signal, stop_loss, take_profit

# ====================================================
# MAIN EXECUTION
# ====================================================

if __name__ == "__main__":
    print("==========================================================")
    print("   CRYPTO BOT ENGINE - STEP 4 RISK MANAGEMENT & TARGETS   ")
    print("==========================================================")

    print("\nScanning Top Volume Coins with SL/TP Targets...\n")
    print(f"{'COIN':<8} | {'PRICE ($)':<10} | {'SIGNAL':<8} | {'STOP LOSS ($)':<13} | {'TAKE PROFIT ($)':<14} | {'R:R RATIO'}")
    print("-" * 78)

    coins = get_top_binance_coins(limit=6)
    for coin in coins:
        price, score, signal, sl, tp = scan_symbol(coin, "1")
        rr = "1:2" if sl > 0 else "N/A"
        print(f"{coin:<8} | ${price:<9,.4f} | {signal:<8} | ${sl:<12,.4f} | ${tp:<13,.4f} | {rr}")
        time.sleep(0.3)

    print("\n[SUCCESS] Step 4 Risk Management Complete!")
