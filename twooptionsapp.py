"""
I would like to create a streamlit app
that accept a ticker, an option type (call/put) and two expiration dates,
that download two option chains from yfinance
and that present option mid prices and intrinsic values of the two option chains within a strike range of 95 to 105% of the underlying in an interactive chart
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Function to calculate option mid price and intrinsic value
def calculate_option_values(option_chain, spot_price, option_type):
    option_chain['midPrice'] = (option_chain['ask'] + option_chain['bid']) / 2
    if option_type == 'call':
        option_chain['intrinsicValue'] = option_chain['strike'].apply(lambda x: max(spot_price - x, 0))
    else:
        option_chain['intrinsicValue'] = option_chain['strike'].apply(lambda x: max(x - spot_price, 0))
    return option_chain

# Streamlit app
st.title('Option Chain Comparison App')

# User inputs
ticker = st.text_input('Enter ticker symbol', 'AAPL')
option_type = st.selectbox('Select option type', ['call', 'put'])
expiry_date1 = st.date_input('Select first expiration date', datetime.now() + timedelta(days=30))
expiry_date2 = st.date_input('Select second expiration date', datetime.now() + timedelta(days=60))

if st.button('Generate Chart'):
    # Fetch stock data
    stock = yf.Ticker(ticker)
    spot_price = stock.history(period='1d')['Close'].iloc[-1]

    # Fetch option chains
    option_chain1 = stock.option_chain(expiry_date1.strftime('%Y-%m-%d'))
    option_chain2 = stock.option_chain(expiry_date2.strftime('%Y-%m-%d'))

    # Select call or put options
    if option_type == 'call':
        chain1 = option_chain1.calls
        chain2 = option_chain2.calls
    else:
        chain1 = option_chain1.puts
        chain2 = option_chain2.puts

    # Calculate mid prices and intrinsic values
    chain1 = calculate_option_values(chain1, spot_price, option_type)
    chain2 = calculate_option_values(chain2, spot_price, option_type)

    # Filter strikes within 95-105% of spot price
    lower_bound = spot_price * 0.95
    upper_bound = spot_price * 1.05
    chain1 = chain1[(chain1['strike'] >= lower_bound) & (chain1['strike'] <= upper_bound)]
    chain2 = chain2[(chain2['strike'] >= lower_bound) & (chain2['strike'] <= upper_bound)]

    # Create interactive chart
    fig = go.Figure()

    # Add traces for first expiry date
    fig.add_trace(go.Scatter(x=chain1['strike'], y=chain1['midPrice'], mode='lines+markers', name=f'Mid Price ({expiry_date1})'))
    fig.add_trace(go.Scatter(x=chain1['strike'], y=chain1['intrinsicValue'], mode='lines+markers', name=f'Intrinsic Value ({expiry_date1})'))

    # Add traces for second expiry date
    fig.add_trace(go.Scatter(x=chain2['strike'], y=chain2['midPrice'], mode='lines+markers', name=f'Mid Price ({expiry_date2})'))
    fig.add_trace(go.Scatter(x=chain2['strike'], y=chain2['intrinsicValue'], mode='lines+markers', name=f'Intrinsic Value ({expiry_date2})'))

    # Update layout
    fig.update_layout(
        title=f'{ticker} {option_type.capitalize()} Options Comparison',
        xaxis_title='Strike Price',
        yaxis_title='Option Price',
        legend_title='Option Values',
        hovermode='x unified'
    )

    # Display the chart
    st.plotly_chart(fig, use_container_width=True)

    # Display additional information
    st.write(f"Current {ticker} price: ${spot_price:.2f}")