"""
This Streamlit app:
- Downloads daily OHLC data of SPX from yfinance
- Plots a candlestick chart of SPX in a TradingView-style interactive chart
- Shows a list of methods to detect trend reversals in the sidebar as input
- Finds reversals in the chosen time range using the selected methods
- Presents markers on the chart representing reversals to downtrend and uptrend
- Summarizes the trend reversals in a table
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

# Function to download SPX data
def get_spx_data(start_date, end_date):
    return yf.download('^GSPC', start=start_date, end=end_date, interval='1d')

# Function to plot candlestick chart
def plot_candlestick(data, reversals_up, reversals_down):
    fig = go.Figure(data=[go.Candlestick(x=data.index,
                                         open=data['Open'],
                                         high=data['High'],
                                         low=data['Low'],
                                         close=data['Close'])])
    
    # Add reversal markers
    fig.add_trace(go.Scatter(x=reversals_up.index, y=reversals_up['Low'],
                             mode='markers', name='Uptrend Reversal',
                             marker=dict(symbol='triangle-up', size=10, color='green')))
    fig.add_trace(go.Scatter(x=reversals_down.index, y=reversals_down['High'],
                             mode='markers', name='Downtrend Reversal',
                             marker=dict(symbol='triangle-down', size=10, color='red')))
    
    fig.update_layout(title='SPX Candlestick Chart with Trend Reversals',
                      xaxis_title='Date',
                      yaxis_title='Price',
                      xaxis_rangeslider_visible=False)
    return fig

# Function to detect trend reversals
def detect_reversals(data, method):
    reversals_up = pd.DataFrame()
    reversals_down = pd.DataFrame()
    
    if method == 'Moving Average Crossover':
        data['MA50'] = data['Close'].rolling(window=50).mean()
        data['MA200'] = data['Close'].rolling(window=200).mean()
        reversals_up = data[(data['MA50'] > data['MA200']) & (data['MA50'].shift(1) <= data['MA200'].shift(1))]
        reversals_down = data[(data['MA50'] < data['MA200']) & (data['MA50'].shift(1) >= data['MA200'].shift(1))]
    
    elif method == 'RSI':
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        data['RSI'] = 100 - (100 / (1 + rs))
        reversals_up = data[(data['RSI'] < 30) & (data['RSI'].shift(1) >= 30)]
        reversals_down = data[(data['RSI'] > 70) & (data['RSI'].shift(1) <= 70)]
    
    return reversals_up, reversals_down

# Streamlit app
st.title('SPX Trend Reversal Detector')

# Sidebar inputs
start_date = st.sidebar.date_input('Start Date', datetime.now() - timedelta(days=365))
end_date = st.sidebar.date_input('End Date', datetime.now())
reversal_methods = ['Moving Average Crossover', 'RSI']
selected_method = st.sidebar.selectbox('Select Reversal Detection Method', reversal_methods)

# Download data
spx_data = get_spx_data(start_date, end_date)

# Detect reversals
reversals_up, reversals_down = detect_reversals(spx_data, selected_method)

# Plot chart
chart = plot_candlestick(spx_data, reversals_up, reversals_down)
st.plotly_chart(chart, use_container_width=True)

# Summary table
st.subheader('Trend Reversal Summary')
summary_data = pd.concat([
    reversals_up[['Close']].rename(columns={'Close': 'Uptrend Reversal Price'}),
    reversals_down[['Close']].rename(columns={'Close': 'Downtrend Reversal Price'})
]).sort_index()
st.table(summary_data)
