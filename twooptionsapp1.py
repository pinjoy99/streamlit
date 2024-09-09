"""
This Streamlit app accepts a ticker, option type (call/put) and two expiration dates in the sidebar.
It downloads two option chains from yfinance and presents option mid prices and intrinsic values 
of the two option chains within a strike range of 95% to 105% of the underlying in an interactive chart.
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# Sidebar inputs
ticker = st.sidebar.text_input("Enter ticker symbol:", value="AAPL")
option_type = st.sidebar.selectbox("Select option type:", ["call", "put"])
exp_date1 = st.sidebar.date_input("Select first expiration date:")
exp_date2 = st.sidebar.date_input("Select second expiration date:")

# Download data
@st.cache_data
def get_option_data(ticker, exp_date, option_type):
    stock = yf.Ticker(ticker)
    options = stock.option_chain(exp_date.strftime('%Y-%m-%d'))
    if option_type == "call":
        return options.calls
    else:
        return options.puts

# Get current stock price
stock = yf.Ticker(ticker)
current_price = stock.history(period="1d")['Close'].iloc[-1]

# Get option chains
options1 = get_option_data(ticker, exp_date1, option_type)
options2 = get_option_data(ticker, exp_date2, option_type)

# Filter strikes (95% to 105% of current price)
min_strike = current_price * 0.95
max_strike = current_price * 1.05
options1 = options1[(options1['strike'] >= min_strike) & (options1['strike'] <= max_strike)]
options2 = options2[(options2['strike'] >= min_strike) & (options2['strike'] <= max_strike)]

# Calculate mid price and intrinsic value
def calculate_values(df, current_price, option_type):
    df['midPrice'] = (df['bid'] + df['ask']) / 2
    if option_type == "call":
        df['intrinsicValue'] = np.maximum(current_price - df['strike'], 0)
    else:
        df['intrinsicValue'] = np.maximum(df['strike'] - current_price, 0)
    return df

options1 = calculate_values(options1, current_price, option_type)
options2 = calculate_values(options2, current_price, option_type)

# Create interactive chart
fig = go.Figure()

fig.add_trace(go.Scatter(x=options1['strike'], y=options1['midPrice'],
                         mode='lines+markers', name=f'Mid Price ({exp_date1})'))
fig.add_trace(go.Scatter(x=options1['strike'], y=options1['intrinsicValue'],
                         mode='lines+markers', name=f'Intrinsic Value ({exp_date1})'))
fig.add_trace(go.Scatter(x=options2['strike'], y=options2['midPrice'],
                         mode='lines+markers', name=f'Mid Price ({exp_date2})'))
fig.add_trace(go.Scatter(x=options2['strike'], y=options2['intrinsicValue'],
                         mode='lines+markers', name=f'Intrinsic Value ({exp_date2})'))

fig.update_layout(title=f'{ticker} {option_type.capitalize()} Options',
                  xaxis_title='Strike Price',
                  yaxis_title='Price',
                  legend_title='Legend')

# Display the chart
st.plotly_chart(fig)

# Display current stock price
st.write(f"Current {ticker} stock price: ${current_price:.2f}")
