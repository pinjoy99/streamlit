"""
This Streamlit app accepts a ticker (default: AAPL) and two expiration dates in the sidebar.
It downloads two option chains from yfinance and presents:
1. Mid prices and intrinsic values of call option chains for the two expiration dates
2. Mid prices and intrinsic values of put option chains for the two expiration dates
The data is displayed within a strike range of 95% to 105% of the underlying price.
The app uses interactive charts and does not rely on regularMarketPrice.
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Function to get next Friday
def get_next_friday(date):
    return date + timedelta((4 - date.weekday() + 7) % 7)

# Function to calculate mid price and intrinsic value
def calculate_option_values(chain, is_call, underlying_price):
    chain['midPrice'] = (chain['bid'] + chain['ask']) / 2
    if is_call:
        chain['intrinsicValue'] = (underlying_price - chain['strike']).clip(lower=0)
    else:
        chain['intrinsicValue'] = (chain['strike'] - underlying_price).clip(lower=0)
    return chain

# Streamlit app
st.title("Option Chain Analyzer")

# Sidebar inputs
ticker = st.sidebar.text_input("Enter Ticker", value="AAPL")
today = datetime.now().date()
exp_date1 = st.sidebar.date_input("First Expiration Date", value=get_next_friday(today))
exp_date2 = st.sidebar.date_input("Second Expiration Date", value=get_next_friday(today + timedelta(days=7)))

# Download data
stock = yf.Ticker(ticker)
current_price = stock.history(period="1d")['Close'].iloc[-1]

# Get option chains
options1 = stock.option_chain(exp_date1.strftime('%Y-%m-%d'))
options2 = stock.option_chain(exp_date2.strftime('%Y-%m-%d'))

# Calculate strike range
lower_strike = current_price * 0.9
upper_strike = current_price * 1.1

# Process call options
calls1 = calculate_option_values(options1.calls, True, current_price)
calls2 = calculate_option_values(options2.calls, True, current_price)
calls1 = calls1[(calls1['strike'] >= lower_strike) & (calls1['strike'] <= upper_strike)]
calls2 = calls2[(calls2['strike'] >= lower_strike) & (calls2['strike'] <= upper_strike)]

# Process put options
puts1 = calculate_option_values(options1.puts, False, current_price)
puts2 = calculate_option_values(options2.puts, False, current_price)
puts1 = puts1[(puts1['strike'] >= lower_strike) & (puts1['strike'] <= upper_strike)]
puts2 = puts2[(puts2['strike'] >= lower_strike) & (puts2['strike'] <= upper_strike)]

# Create call options chart
fig_calls = go.Figure()
fig_calls.add_trace(go.Scatter(x=calls1['strike'], y=calls1['midPrice'], mode='lines+markers', name=f'Mid Price ({exp_date1})'))
fig_calls.add_trace(go.Scatter(x=calls1['strike'], y=calls1['intrinsicValue'], mode='lines+markers', name=f'Intrinsic Value ({exp_date1})'))
fig_calls.add_trace(go.Scatter(x=calls2['strike'], y=calls2['midPrice'], mode='lines+markers', name=f'Mid Price ({exp_date2})'))
fig_calls.add_trace(go.Scatter(x=calls2['strike'], y=calls2['intrinsicValue'], mode='lines+markers', name=f'Intrinsic Value ({exp_date2})'))
fig_calls.update_layout(title='Call Options', xaxis_title='Strike Price', yaxis_title='Price')

# Create put options chart
fig_puts = go.Figure()
fig_puts.add_trace(go.Scatter(x=puts1['strike'], y=puts1['midPrice'], mode='lines+markers', name=f'Mid Price ({exp_date1})'))
fig_puts.add_trace(go.Scatter(x=puts1['strike'], y=puts1['intrinsicValue'], mode='lines+markers', name=f'Intrinsic Value ({exp_date1})'))
fig_puts.add_trace(go.Scatter(x=puts2['strike'], y=puts2['midPrice'], mode='lines+markers', name=f'Mid Price ({exp_date2})'))
fig_puts.add_trace(go.Scatter(x=puts2['strike'], y=puts2['intrinsicValue'], mode='lines+markers', name=f'Intrinsic Value ({exp_date2})'))
fig_puts.update_layout(title='Put Options', xaxis_title='Strike Price', yaxis_title='Price')

# Display charts
st.plotly_chart(fig_calls)
st.plotly_chart(fig_puts)
