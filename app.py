import streamlit as st
import pandas as pd
import requests

# --- SETUP ---
st.set_page_config(page_title="Sniper Radar", page_icon="🎯")
st.title("🎯 Sniper Radar (Manual MT5)")
st.write("Strict Harami & Tsutsumi Scanner for Gold, BTC, and Forex.")

# This pulls the key from your Streamlit Secrets box
try:
    API_KEY = st.secrets["TWELVEDATA_API_KEY"]
except:
    st.error("⚠️ API Key not found in Streamlit Secrets! Please check your settings.")
    st.stop()

SYMBOLS = ["XAU/USD", "BTC/USD", "EUR/USD", "GBP/USD"]

def get_data(symbol):
    # Fetching 50 candles of 15-minute data
    url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval=15min&outputsize=50&apikey={API_KEY}"
    response = requests.get(url).json()
    
    # Check for API errors (like limit reached or invalid key)
    if "status" in response and response["status"] == "error":
        return response["message"]
        
    if "values" not in response:
        return "Unknown API Error"
        
    df = pd.DataFrame(response["values"])
    for col in ['open', 'high', 'low', 'close', 'volume']:
        df[col] = df[col].astype(float)
    df = df.iloc[::-1].reset_index(drop=True)
    return df

def analyze_market(df, symbol):
    df['EMA9'] = df['close'].ewm(span=9, adjust=False).mean()
    df['EMA21'] = df['close'].ewm(span=21, adjust=False).mean()
    
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    df['Vol_SMA'] = df['volume'].rolling(window=20).mean()
    df['RVOL'] = df['volume'] / df['Vol_SMA']
    
    prev_open, prev_close = df['open'].iloc[-2], df['close'].iloc[-2]
    curr_open, curr_close = df['open'].iloc[-1], df['close'].iloc[-1]
    
    prev_body = abs(prev_close - prev_open)
    curr_body = abs(curr_close - curr_open)
    
    is_harami = (prev_close < prev_open) and (curr_close > curr_open) and \
                (curr_open > prev_close) and (curr_close < prev_open) and \
                (curr_body < prev_body * 0.5)
                
    is_tsutsumi = (prev_close < prev_open) and (curr_close > curr_open) and \
                  (curr_open <= prev_close) and (curr_close >= prev_open)
                  
    latest = df.iloc[-1]
    
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
    with st.spinner("Fetching data and scanning patterns..."):
        for symbol in SYMBOLS:
            data_result = get_data(symbol)
            
            # If it's a string, it means an error message was returned
            if isinstance(data_result, str):
                st.error(f"**{symbol}**: Failed - {data_result}")
            else:
                signal, reason, price, rsi, rvol = analyze_market(data_result, symbol)
                
                if signal == "SAFE BUY":
                    st.success(f"**{symbol}**: {signal} - {reason} | Price: {price} | RSI: {rsi:.1f} | Vol: {rvol:.1f}x")
                elif signal == "BAD TRAP":
                    st.error(f"**{symbol}**: {signal} - {reason} | Price: {price} | RSI: {rsi:.1f}")
                else:
                    st.warning(f"**{symbol}**: {signal} - {reason} | Price: {price} | RSI: {rsi:.1f}")
