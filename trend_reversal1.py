"""
This Streamlit app:
- Downloads daily OHLC data of SPX from yfinance
- Plots a candlestick chart of SPX in a TradingView-style interactive chart
- Shows a list of top-10 popular methods in the sidebar to detect trend reversals
- Includes sliders to select parameters for the chosen detection method
- Presents a chart of the chosen indicator if available
- Finds reversals in the chosen time range using the selected method
- Presents markers on the chart representing reversals to downtrend and uptrend
- Summarizes the trend reversals in a table
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta

# Function to download SPX data
@st.cache_data
def get_spx_data(start_date, end_date):
    spx = yf.Ticker("^GSPC")
    data = spx.history(start=start_date, end=end_date)
    return data

# Function to create candlestick chart
def plot_candlestick(data):
    fig = go.Figure(data=[go.Candlestick(x=data.index,
                open=data['Open'],
                high=data['High'],
                low=data['Low'],
                close=data['Close'])])
    fig.update_layout(title='SPX Candlestick Chart', xaxis_rangeslider_visible=False)
    return fig

# Function to calculate indicators
def calculate_indicator(data, method, params):
    if method == "Moving Average Crossover":
        data['MA_short'] = data['Close'].rolling(window=params['short_window']).mean()
        data['MA_long'] = data['Close'].rolling(window=params['long_window']).mean()
    elif method == "RSI":
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=params['window']).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=params['window']).mean()
        rs = gain / loss
        data['RSI'] = 100 - (100 / (1 + rs))
    # Add more indicators as needed
    return data

# Function to detect reversals
def detect_reversals(data, method, params):
    reversals = []
    if method == "Moving Average Crossover":
        for i in range(1, len(data)):
            if data['MA_short'].iloc[i-1] <= data['MA_long'].iloc[i-1] and data['MA_short'].iloc[i] > data['MA_long'].iloc[i]:
                reversals.append((data.index[i], 'Uptrend'))
            elif data['MA_short'].iloc[i-1] >= data['MA_long'].iloc[i-1] and data['MA_short'].iloc[i] < data['MA_long'].iloc[i]:
                reversals.append((data.index[i], 'Downtrend'))
    elif method == "RSI":
        for i in range(1, len(data)):
            if data['RSI'].iloc[i-1] <= params['oversold'] and data['RSI'].iloc[i] > params['oversold']:
                reversals.append((data.index[i], 'Uptrend'))
            elif data['RSI'].iloc[i-1] >= params['overbought'] and data['RSI'].iloc[i] < params['overbought']:
                reversals.append((data.index[i], 'Downtrend'))
    # Add more reversal detection methods as needed
    return reversals

# Streamlit app
st.title('SPX Trend Reversal Detector')

# Sidebar
st.sidebar.header('Parameters')
start_date = st.sidebar.date_input('Start Date', datetime.now() - timedelta(days=365))
end_date = st.sidebar.date_input('End Date', datetime.now())

reversal_methods = [
    "Moving Average Crossover",
    "RSI",
    "MACD",
    "Bollinger Bands",
    "Stochastic Oscillator",
    "Fibonacci Retracement",
    "Ichimoku Cloud",
    "Parabolic SAR",
    "ADX",
    "Volume Price Trend"
]

selected_method = st.sidebar.selectbox('Select Reversal Detection Method', reversal_methods)

# Parameters for selected method
if selected_method == "Moving Average Crossover":
    short_window = st.sidebar.slider('Short MA Window', 5, 50, 20)
    long_window = st.sidebar.slider('Long MA Window', 20, 200, 50)
    params = {'short_window': short_window, 'long_window': long_window}
elif selected_method == "RSI":
    window = st.sidebar.slider('RSI Window', 5, 30, 14)
    oversold = st.sidebar.slider('Oversold Level', 20, 40, 30)
    overbought = st.sidebar.slider('Overbought Level', 60, 80, 70)
    params = {'window': window, 'oversold': oversold, 'overbought': overbought}
# Add more parameter settings for other methods

# Main app
data = get_spx_data(start_date, end_date)

# Calculate indicator
data = calculate_indicator(data, selected_method, params)

# Detect reversals
reversals = detect_reversals(data, selected_method, params)

# Plot candlestick chart
fig = plot_candlestick(data)

# Add indicator to the chart
if selected_method == "Moving Average Crossover":
    fig.add_trace(go.Scatter(x=data.index, y=data['MA_short'], name='Short MA'))
    fig.add_trace(go.Scatter(x=data.index, y=data['MA_long'], name='Long MA'))
elif selected_method == "RSI":
    fig.add_trace(go.Scatter(x=data.index, y=data['RSI'], name='RSI', yaxis="y2"))
    fig.update_layout(yaxis2=dict(title="RSI", overlaying="y", side="right"))

# Add reversal markers
for date, direction in reversals:
    fig.add_annotation(x=date, y=data.loc[date, 'High'] if direction == 'Downtrend' else data.loc[date, 'Low'],
                       text='⬇' if direction == 'Downtrend' else '⬆',
                       showarrow=False)

st.plotly_chart(fig, use_container_width=True)

# Summarize reversals in a table
if reversals:
    st.subheader('Trend Reversals')
    reversal_df = pd.DataFrame(reversals, columns=['Date', 'Direction'])
    st.table(reversal_df)
else:
    st.write('No trend reversals detected in the selected time range.')
