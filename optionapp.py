import yfinance as yf
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Function to download option chain data
def get_option_chain(ticker, expiration):
    stock = yf.Ticker(ticker)
    options = stock.option_chain(expiration)
    return options.calls, options.puts

# Function to calculate mid prices and intrinsic values
def calculate_values(calls, puts, underlying_price):
    calls['mid_price'] = (calls['bid'] + calls['ask']) / 2
    puts['mid_price'] = (puts['bid'] + puts['ask']) / 2
    
    calls['intrinsic_value'] = np.maximum(0, underlying_price - calls['strike'])
    puts['intrinsic_value'] = np.maximum(0, puts['strike'] - underlying_price)
    
    return calls, puts

# Streamlit app
st.title("Option Chain Analysis")

# User inputs
ticker = st.text_input("Enter the ticker symbol", "AAPL")
expiration = st.selectbox("Select expiration date", yf.Ticker(ticker).options)
underlying_price = yf.Ticker(ticker).history(period="1d")['Close'].iloc[-1]
strike_range = st.slider("Select strike range (% of underlying)", 80, 120, (80, 120))

# Download and process data
calls, puts = get_option_chain(ticker, expiration)
calls, puts = calculate_values(calls, puts, underlying_price)

# Filter by strike range
strike_min = underlying_price * (strike_range[0] / 100)
strike_max = underlying_price * (strike_range[1] / 100)
calls_filtered = calls[(calls['strike'] >= strike_min) & (calls['strike'] <= strike_max)]
puts_filtered = puts[(puts['strike'] >= strike_min) & (puts['strike'] <= strike_max)]

# Display tables
st.subheader("Call Options")
st.dataframe(calls_filtered[['strike', 'mid_price', 'intrinsic_value']])

st.subheader("Put Options")
st.dataframe(puts_filtered[['strike', 'mid_price', 'intrinsic_value']])

# Plot mid prices and intrinsic values
fig, ax = plt.subplots()
ax.plot(calls_filtered['strike'], calls_filtered['mid_price'], label='Call Mid Price', marker='o')
ax.plot(puts_filtered['strike'], puts_filtered['mid_price'], label='Put Mid Price', marker='x')
ax.plot(calls_filtered['strike'], calls_filtered['intrinsic_value'], label='Call Intrinsic Value', linestyle='--')
ax.plot(puts_filtered['strike'], puts_filtered['intrinsic_value'], label='Put Intrinsic Value', linestyle='--')
ax.set_xlabel('Strike Price')
ax.set_ylabel('Price')
ax.legend()
st.pyplot(fig)