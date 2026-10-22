import streamlit as st
import pandas as pd
import requests

# --- SETUP ---
st.set_page_config(page_title="Sniper Radar", page_icon="🎯")
st.title("🎯 Sniper Radar (Manual MT5)")
st.write("Strict Harami & Tsutsumi Scanner for Gold, BTC, and Forex.")

# Put your TwelveData API key here
API_KEY = "PK7LMWASVEN5MB6TC67AY4HMII" 
SYMBOLS = ["XAU/USD", "BTC/USD", "EUR/USD", "GBP/USD"]

def get_data(symbol):
    # Fetching 50 candles of 15-minute data
    url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval=15min&outputsize=50&apikey={API_KEY}"
    response = requests.get(url).json()
    
    if "values" not in response:
        return None
        
    df = pd.DataFrame(response["values"])
    # Convert strings to floats and reverse order (oldest to newest)
    for col in ['open', 'high', 'low', 'close', 'volume']:
        df[col] = df[col].astype(float)
    df = df.iloc[::-1].reset_index(drop=True)
    return df

def analyze_market(df, symbol):
    # 1. Calculate Indicators
    df['EMA9'] = df['close'].ewm(span=9, adjust=False).mean()
    df['EMA21'] = df['close'].ewm(span=21, adjust=False).mean()
    
    # RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # RVOL
    df['Vol_SMA'] = df['volume'].rolling(window=20).mean()
    df['RVOL'] = df['volume'] / df['Vol_SMA']
    
    # 2. Pattern Recognition (Harami & Tsutsumi)
    prev_open, prev_close = df['open'].iloc[-2], df['close'].iloc[-2]
    curr_open, curr_close = df['open'].iloc[-1], df['close'].iloc[-1]
    
    prev_body = abs(prev_close - prev_open)
    curr_body = abs(curr_close - curr_open)
    
    # Bullish Harami
    is_harami = (prev_close < prev_open) and (curr_close > curr_open) and \
                (curr_open > prev_close) and (curr_close < prev_open) and \
                (curr_body < prev_body * 0.5)
                
    # Bullish Tsutsumi (Engulfing)
    is_tsutsumi = (prev_close < prev_open) and (curr_close > curr_open) and \
                  (curr_open <= prev_close) and (curr_close >= prev_open)
                  
    latest = df.iloc[-1]
    
    # 3. Strict Logic Evaluation
    if is_harami and latest['RSI'] < 40:
        return "SAFE BUY", "Harami Reversal", latest['close'], latest['RSI'], latest['RVOL']
    elif is_tsutsumi and latest['RVOL'] > 1.2 and latest['RSI'] < 65:
        return "SAFE BUY", "Tsutsumi Breakout", latest['close'], latest['RSI'], latest['RVOL']
    elif latest['RSI'] > 70:
        return "BAD TRAP", "Overbought", latest['close'], latest['RSI'], latest['RVOL']
    else:
        return "WAIT", "No Setup", latest['close'], latest['RSI'], latest['RVOL']

# --- UI LOGIC ---
if st.button("SCAN MARKET NOW", use_container_width=True):
    if API_KEY == "YOUR_API_KEY_HERE":
        st.error("Please insert your API Key in the code.")
    else:
        for symbol in SYMBOLS:
            df = get_data(symbol)
            if df is not None:
                signal, reason, price, rsi, rvol = analyze_market(df, symbol)
                
                # Display colored boxes based on signal
                if signal == "SAFE BUY":
                    st.success(f"**{symbol}**: {signal} - {reason} | Price: {price} | RSI: {rsi:.1f} | Vol: {rvol:.1f}x")
                elif signal == "BAD TRAP":
                    st.error(f"**{symbol}**: {signal} - {reason} | Price: {price} | RSI: {rsi:.1f}")
                else:
                    st.warning(f"**{symbol}**: {signal} - {reason} | Price: {price} | RSI: {rsi:.1f}")
