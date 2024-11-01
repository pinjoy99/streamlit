# -*- coding: utf-8 -*-
"""
Create a streamlit app that:
1. Downloads historical data of a chosen stock ticker among top 30 most traded stocks and ETFs for a chosen time range (default 4 years) shown in the side bar
2. Backtests long-only stock trading strategies based on a chosen indicator and parameters shown in the side bar among top-10 most popular TA indicators including but not limited to SMA crossover, MACD, RSI, ATR using ta package
3. Presents an interactive plot of a subplot showing stock-price line chart with buy/sell markers, a subplot showing gain/loss chart as well as a benchmark of buy-and-hold, and a subplot showing the indicator chart with buy/sell signals
4. Creates a table showing the details of individual trades including holding positions, proceeds per trade and a cumulative profit/loss
5. Includes the metrics to compare the chosen strategy with the Buy & Hold including total return, CAGR, MDD, Max Loss, Win rate, etc.
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from ta import add_all_ta_features
from ta.utils import dropna
from datetime import datetime, timedelta

# List of top 30 most traded stocks and ETFs
tickers = ['AAPL', 'MSFT', 'AMZN', 'GOOGL', 'META', 'TSLA', 'NVDA', 'JPM', 'V', 'JNJ',
           'WMT', 'PG', 'UNH', 'HD', 'BAC', 'MA', 'DIS', 'ADBE', 'CRM', 'NFLX',
           'CMCSA', 'XOM', 'VZ', 'CSCO', 'PFE', 'INTC', 'KO', 'PEP', 'T', 'MRK']

# List of indicators
indicators = ['SMA Crossover', 'MACD', 'RSI', 'ATR']

# Sidebar
st.sidebar.title('Stock Analysis App')
ticker = st.sidebar.selectbox('Select a stock', tickers)
#end_date = datetime.now()
#start_date = end_date - timedelta(days=4*365)
date_range = st.sidebar.date_input('Select date range', [start_date, end_date])
indicator = st.sidebar.selectbox('Select an indicator', indicators)

# Download data
@st.cache_data
def load_data(ticker, start, end):
    data = yf.download(ticker, start=start, end=end)
    data = dropna(data)
    data = add_all_ta_features(data, open="Open", high="High", low="Low", close="Close", volume="Volume")
    return data

data = load_data(ticker, date_range[0], date_range[1])

# Strategy parameters
if indicator == 'SMA Crossover':
    short_window = st.sidebar.slider('Short window', 10, 100, 50)
    long_window = st.sidebar.slider('Long window', 20, 200, 200)
    data['Signal'] = np.where(data[f'trend_sma_{short_window}'] > data[f'trend_sma_{long_window}'], 1, 0)
elif indicator == 'MACD':
    fast = st.sidebar.slider('Fast period', 12, 26, 12)
    slow = st.sidebar.slider('Slow period', 26, 40, 26)
    signal = st.sidebar.slider('Signal period', 9, 15, 9)
    data['Signal'] = np.where(data[f'trend_macd_diff_{fast}_{slow}_{signal}'] > 0, 1, 0)
elif indicator == 'RSI':
    rsi_period = st.sidebar.slider('RSI period', 2, 30, 14)
    overbought = st.sidebar.slider('Overbought level', 70, 90, 70)
    oversold = st.sidebar.slider('Oversold level', 10, 30, 30)
    data['Signal'] = np.where(data[f'momentum_rsi_{rsi_period}'] < oversold, 1, 0)
    data['Signal'] = np.where(data[f'momentum_rsi_{rsi_period}'] > overbought, 0, data['Signal'])
elif indicator == 'ATR':
    atr_period = st.sidebar.slider('ATR period', 10, 50, 14)
    multiplier = st.sidebar.slider('ATR multiplier', 1.0, 5.0, 2.0)
    data['ATR'] = data[f'volatility_atr_{atr_period}']
    data['Upper_Band'] = data['Close'] + multiplier * data['ATR']
    data['Lower_Band'] = data['Close'] - multiplier * data['ATR']
    data['Signal'] = np.where(data['Close'] > data['Upper_Band'].shift(1), 1, 0)
    data['Signal'] = np.where(data['Close'] < data['Lower_Band'].shift(1), 0, data['Signal'])

# Calculate returns
data['Strategy_Returns'] = data['Signal'].shift(1) * data['Close'].pct_change()
data['Cumulative_Strategy_Returns'] = (1 + data['Strategy_Returns']).cumprod()
data['Buy_Hold_Returns'] = data['Close'].pct_change()
data['Cumulative_Buy_Hold_Returns'] = (1 + data['Buy_Hold_Returns']).cumprod()

# Create plot
fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.05, subplot_titles=('Stock Price', 'Returns', 'Indicator'))

# Stock price subplot
fig.add_trace(go.Scatter(x=data.index, y=data['Close'], name='Close Price'), row=1, col=1)
buy_signals = data[data['Signal'] == 1]
sell_signals = data[data['Signal'].shift(1) == 1][data['Signal'] == 0]
fig.add_trace(go.Scatter(x=buy_signals.index, y=buy_signals['Close'], mode='markers', name='Buy Signal', marker=dict(symbol='triangle-up', size=10, color='green')), row=1, col=1)
fig.add_trace(go.Scatter(x=sell_signals.index, y=sell_signals['Close'], mode='markers', name='Sell Signal', marker=dict(symbol='triangle-down', size=10, color='red')), row=1, col=1)

# Returns subplot
fig.add_trace(go.Scatter(x=data.index, y=data['Cumulative_Strategy_Returns'], name='Strategy Returns'), row=2, col=1)
fig.add_trace(go.Scatter(x=data.index, y=data['Cumulative_Buy_Hold_Returns'], name='Buy & Hold Returns'), row=2, col=1)

# Indicator subplot
if indicator == 'SMA Crossover':
    fig.add_trace(go.Scatter(x=data.index, y=data[f'trend_sma_{short_window}'], name=f'SMA {short_window}'), row=3, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data[f'trend_sma_{long_window}'], name=f'SMA {long_window}'), row=3, col=1)
elif indicator == 'MACD':
    fig.add_trace(go.Scatter(x=data.index, y=data[f'trend_macd_{fast}_{slow}_{signal}'], name='MACD'), row=3, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data[f'trend_macd_signal_{fast}_{slow}_{signal}'], name='Signal'), row=3, col=1)
elif indicator == 'RSI':
    fig.add_trace(go.Scatter(x=data.index, y=data[f'momentum_rsi_{rsi_period}'], name='RSI'), row=3, col=1)
    fig.add_hline(y=overbought, line_dash="dash", line_color="red", row=3, col=1)
    fig.add_hline(y=oversold, line_dash="dash", line_color="green", row=3, col=1)
elif indicator == 'ATR':
    fig.add_trace(go.Scatter(x=data.index, y=data['Upper_Band'], name='Upper Band'), row=3, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data['Lower_Band'], name='Lower Band'), row=3, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'], name='Close Price'), row=3, col=1)

fig.update_layout(height=900, title_text=f"{ticker} Stock Analysis")
st.plotly_chart(fig, use_container_width=True)

# Trade details
trades = pd.DataFrame(columns=['Entry Date', 'Exit Date', 'Entry Price', 'Exit Price', 'Shares', 'Profit/Loss', 'Cumulative P/L'])
in_position = False
entry_date = None
entry_price = None
shares = 0
cumulative_pl = 0

for i in range(1, len(data)):
    if not in_position and data['Signal'].iloc[i] == 1:
        in_position = True
        entry_date = data.index[i]
        entry_price = data['Close'].iloc[i]
        shares = 1000 // entry_price  # Assuming $1000 investment per trade
    elif in_position and data['Signal'].iloc[i] == 0:
        in_position = False
        exit_date = data.index[i]
        exit_price = data['Close'].iloc[i]
        pl = (exit_price - entry_price) * shares
        cumulative_pl += pl
        trades = trades.append({
            'Entry Date': entry_date,
            'Exit Date': exit_date,
            'Entry Price': entry_price,
            'Exit Price': exit_price,
            'Shares': shares,
            'Profit/Loss': pl,
            'Cumulative P/L': cumulative_pl
        }, ignore_index=True)

st.subheader('Trade Details')
st.dataframe(trades)

# Performance metrics
total_return_strategy = data['Cumulative_Strategy_Returns'].iloc[-1] - 1
total_return_bh = data['Cumulative_Buy_Hold_Returns'].iloc[-1] - 1
cagr_strategy = (data['Cumulative_Strategy_Returns'].iloc[-1] ** (365 / len(data)) - 1) * 100
cagr_bh = (data['Cumulative_Buy_Hold_Returns'].iloc[-1] ** (365 / len(data)) - 1) * 100
mdd_strategy = (data['Cumulative_Strategy_Returns'] / data['Cumulative_Strategy_Returns'].cummax() - 1).min() * 100
mdd_bh = (data['Cumulative_Buy_Hold_Returns'] / data['Cumulative_Buy_Hold_Returns'].cummax() - 1).min() * 100
max_loss_strategy = data['Strategy_Returns'].min() * 100
max_loss_bh = data['Buy_Hold_Returns'].min() * 100
win_rate = (trades['Profit/Loss'] > 0).mean() * 100

st.subheader('Performance Metrics')
metrics = pd.DataFrame({
    'Metric': ['Total Return', 'CAGR', 'Max Drawdown', 'Max Loss'],
    'Strategy': [f'{total_return_strategy:.2%}', f'{cagr_strategy:.2f}%', f'{mdd_strategy:.2f}%', f'{max_loss_strategy:.2f}%'],
    'Buy & Hold': [f'{total_return_bh:.2%}', f'{cagr_bh:.2f}%', f'{mdd_bh:.2f}%', f'{max_loss_bh:.2f}%']
})
st.dataframe(metrics)
st.write(f'Win Rate: {win_rate:.2f}%')
