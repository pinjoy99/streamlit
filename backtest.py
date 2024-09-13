import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from ta.trend import MACD
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange

# Define the list of top 20 most traded stocks and ETFs
top_tickers = ['AAPL', 'MSFT', 'AMZN', 'GOOGL', 'FB', 'TSLA', 'NVDA', 'JPM', 'JNJ', 'V', 
               'PG', 'UNH', 'HD', 'BAC', 'DIS', 'ADBE', 'CRM', 'NFLX', 'CMCSA', 'PFE']

# Sidebar inputs
st.sidebar.header('Input Parameters')
ticker = st.sidebar.selectbox('Select Stock Ticker', top_tickers)
years = st.sidebar.slider('Select Number of Years', 1, 10, 4)
end_date = pd.Timestamp.now()
start_date = end_date - pd.DateOffset(years=years)

indicator = st.sidebar.selectbox('Select Indicator', ['MACD', 'RSI', 'ATR'])

if indicator == 'MACD':
    fast_period = st.sidebar.slider('Fast Period', 5, 50, 12)
    slow_period = st.sidebar.slider('Slow Period', 10, 100, 26)
    signal_period = st.sidebar.slider('Signal Period', 5, 20, 9)
elif indicator == 'RSI':
    rsi_period = st.sidebar.slider('RSI Period', 5, 30, 14)
    overbought = st.sidebar.slider('Overbought Level', 70, 90, 70)
    oversold = st.sidebar.slider('Oversold Level', 10, 30, 30)
elif indicator == 'ATR':
    atr_period = st.sidebar.slider('ATR Period', 5, 30, 14)
    atr_multiplier = st.sidebar.slider('ATR Multiplier', 1.0, 5.0, 2.0, 0.1)

# Download data
@st.cache_data
def download_data(ticker, start_date, end_date):
    data = yf.download(ticker, start=start_date, end=end_date)
    return data

data = download_data(ticker, start_date, end_date)

# Calculate indicators
if indicator == 'MACD':
    macd = MACD(data['Close'], window_fast=fast_period, window_slow=slow_period, window_sign=signal_period)
    data['MACD'] = macd.macd()
    data['Signal'] = macd.macd_signal()
    data['MACD_Hist'] = macd.macd_diff()
    buy_signal = (data['MACD'] > data['Signal']) & (data['MACD'].shift(1) <= data['Signal'].shift(1))
    sell_signal = (data['MACD'] < data['Signal']) & (data['MACD'].shift(1) >= data['Signal'].shift(1))
elif indicator == 'RSI':
    rsi = RSIIndicator(data['Close'], window=rsi_period)
    data['RSI'] = rsi.rsi()
    buy_signal = (data['RSI'] < oversold) & (data['RSI'].shift(1) >= oversold)
    sell_signal = (data['RSI'] > overbought) & (data['RSI'].shift(1) <= overbought)
elif indicator == 'ATR':
    atr = AverageTrueRange(data['High'], data['Low'], data['Close'], window=atr_period)
    data['ATR'] = atr.average_true_range()
    data['Upper_Band'] = data['Close'] + atr_multiplier * data['ATR']
    data['Lower_Band'] = data['Close'] - atr_multiplier * data['ATR']
    buy_signal = (data['Close'] > data['Upper_Band']) & (data['Close'].shift(1) <= data['Upper_Band'].shift(1))
    sell_signal = (data['Close'] < data['Lower_Band']) & (data['Close'].shift(1) >= data['Lower_Band'].shift(1))

# Backtesting
data['Position'] = np.nan
data.loc[buy_signal, 'Position'] = 1
data.loc[sell_signal, 'Position'] = 0
data['Position'] = data['Position'].fillna(method='ffill')
data['Strategy_Returns'] = data['Position'].shift(1) * data['Close'].pct_change()
data['Cumulative_Returns'] = (1 + data['Strategy_Returns']).cumprod()
data['Buy_and_Hold_Returns'] = (1 + data['Close'].pct_change()).cumprod()

# Create interactive plot
fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.05, 
                    subplot_titles=('Stock Price', 'Cumulative Returns', indicator))

fig.add_trace(go.Scatter(x=data.index, y=data['Close'], name='Close Price'), row=1, col=1)
fig.add_trace(go.Scatter(x=data.index, y=data['Cumulative_Returns'], name='Strategy Returns'), row=2, col=1)
fig.add_trace(go.Scatter(x=data.index, y=data['Buy_and_Hold_Returns'], name='Buy and Hold Returns'), row=2, col=1)

if indicator == 'MACD':
    fig.add_trace(go.Scatter(x=data.index, y=data['MACD'], name='MACD'), row=3, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data['Signal'], name='Signal'), row=3, col=1)
    fig.add_bar(x=data.index, y=data['MACD_Hist'], name='MACD Histogram', row=3, col=1)
elif indicator == 'RSI':
    fig.add_trace(go.Scatter(x=data.index, y=data['RSI'], name='RSI'), row=3, col=1)
    fig.add_hline(y=overbought, line_dash="dash", line_color="red", row=3, col=1)
    fig.add_hline(y=oversold, line_dash="dash", line_color="green", row=3, col=1)
elif indicator == 'ATR':
    fig.add_trace(go.Scatter(x=data.index, y=data['Upper_Band'], name='Upper Band'), row=3, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data['Lower_Band'], name='Lower Band'), row=3, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'], name='Close Price'), row=3, col=1)

buy_points = data[buy_signal]
sell_points = data[sell_signal]

fig.add_trace(go.Scatter(x=buy_points.index, y=buy_points['Close'], mode='markers', 
                         marker=dict(symbol='triangle-up', size=10, color='green'), 
                         name='Buy Signal'), row=1, col=1)
fig.add_trace(go.Scatter(x=sell_points.index, y=sell_points['Close'], mode='markers', 
                         marker=dict(symbol='triangle-down', size=10, color='red'), 
                         name='Sell Signal'), row=1, col=1)

fig.update_layout(height=900, title
