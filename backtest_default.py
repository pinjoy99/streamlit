# """
# Create a streamlit app that
# downloads historical data of a chosen stock ticker among top 30 most traded stocks and ETFs for a chosen time range (default 4 years) shown in the side bar,

# backtests long-only stock trading strategies 
# based on a chosen indicator and parameters shown in the side bar among well-known TA indicators, such as SMA crossover, MACD, RSI, ATR using ta,

# presents an interactive plot of a subplot showing stock-price line chart with buy/sell markers, a subplot showing gain/loss chart as well as a benchmark of buy-and-hold , and a subplot showing the indicator chart with buy/sell signals,

# creates a table showing the details of individual trades including holding positions,   proceeds per trade and a cumulative profit/loss.

# includes the metrics to compare the chosen strategy with the Buy & Hold including total return, CAGR, MDD, Max Loss, Win rate, etc.
# """

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from ta.trend import SMAIndicator, MACD
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange
from datetime import datetime, timedelta

# List of top 30 most traded stocks and ETFs
tickers = ['AAPL', 'MSFT', 'AMZN', 'GOOGL', 'FB', 'TSLA', 'BRK-B', 'V', 'JNJ', 'WMT', 
           'JPM', 'PG', 'UNH', 'MA', 'DIS', 'NVDA', 'HD', 'BAC', 'VZ', 'ADBE', 
           'CMCSA', 'PFE', 'KO', 'XOM', 'T', 'CSCO', 'PEP', 'INTC', 'CVX', 'MRK']

# Sidebar inputs
st.sidebar.header('Input Parameters')
ticker = st.sidebar.selectbox('Select Stock Ticker', tickers)
end_date = datetime.now().date()
start_date = st.sidebar.date_input('Start Date', end_date - timedelta(days=4*365))
indicator = st.sidebar.selectbox('Select Indicator', ['SMA Crossover', 'MACD', 'RSI', 'ATR'])

# Indicator parameters
if indicator == 'SMA Crossover':
    fast_period = st.sidebar.slider('Fast SMA Period', 5, 50, 20)
    slow_period = st.sidebar.slider('Slow SMA Period', 20, 200, 50)
elif indicator == 'MACD':
    fast_period = st.sidebar.slider('Fast Period', 5, 50, 12)
    slow_period = st.sidebar.slider('Slow Period', 20, 200, 26)
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

# Calculate indicators and signals
def calculate_signals(data, indicator):
    if indicator == 'SMA Crossover':
        data['FastSMA'] = SMAIndicator(data['Close'], window=fast_period).sma_indicator()
        data['SlowSMA'] = SMAIndicator(data['Close'], window=slow_period).sma_indicator()
        data['Signal'] = np.where(data['FastSMA'] > data['SlowSMA'], 1, 0)
    elif indicator == 'MACD':
        macd = MACD(data['Close'], window_fast=fast_period, window_slow=slow_period, window_sign=signal_period)
        data['MACD'] = macd.macd()
        data['Signal'] = macd.macd_signal()
        data['Signal'] = np.where(data['MACD'] > data['Signal'], 1, 0)
    elif indicator == 'RSI':
        data['RSI'] = RSIIndicator(data['Close'], window=rsi_period).rsi()
        data['Signal'] = np.where(data['RSI'] < oversold, 1, np.where(data['RSI'] > overbought, 0, np.nan))
        data['Signal'] = data['Signal'].ffill()
    elif indicator == 'ATR':
        data['ATR'] = AverageTrueRange(data['High'], data['Low'], data['Close'], window=atr_period).average_true_range()
        data['UpperBand'] = data['Close'] + atr_multiplier * data['ATR']
        data['LowerBand'] = data['Close'] - atr_multiplier * data['ATR']
        data['Signal'] = np.where(data['Close'] > data['UpperBand'].shift(1), 1, 
                                  np.where(data['Close'] < data['LowerBand'].shift(1), 0, np.nan))
        data['Signal'] = data['Signal'].ffill()
    
    return data

data = calculate_signals(data, indicator)

# Backtest strategy
def backtest_strategy(data):
    data['Position'] = data['Signal'].shift(1)
    data['Returns'] = data['Close'].pct_change()
    data['Strategy Returns'] = data['Position'] * data['Returns']
    data['Cumulative Returns'] = (1 + data['Strategy Returns']).cumprod()
    data['Buy&Hold Returns'] = (1 + data['Returns']).cumprod()
    
    # Calculate trade details
    data['Trade'] = data['Position'].diff()
    trades = data[data['Trade'] != 0].copy()
    trades['Type'] = np.where(trades['Trade'] > 0, 'Buy', 'Sell')
    trades['Price'] = data['Close']
    trades['Profit/Loss'] = trades.groupby((trades['Trade'] != 0).cumsum())['Price'].transform(lambda x: x.iloc[-1] - x.iloc[0])
    trades['Cumulative P/L'] = trades['Profit/Loss'].cumsum()
    
    return data, trades

data, trades = backtest_strategy(data)

# Create interactive plot
def create_plot(data):
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.05, 
                        subplot_titles=('Stock Price', 'Cumulative Returns', 'Indicator'))
    
    # Stock price chart
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'], name='Close Price'), row=1, col=1)
    fig.add_trace(go.Scatter(x=data[data['Trade'] > 0].index, y=data[data['Trade'] > 0]['Close'], 
                             mode='markers', name='Buy', marker=dict(color='green', symbol='triangle-up', size=10)), row=1, col=1)
    fig.add_trace(go.Scatter(x=data[data['Trade'] < 0].index, y=data[data['Trade'] < 0]['Close'], 
                             mode='markers', name='Sell', marker=dict(color='red', symbol='triangle-down', size=10)), row=1, col=1)
    
    # Cumulative returns chart
    fig.add_trace(go.Scatter(x=data.index, y=data['Cumulative Returns'], name='Strategy'), row=2, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data['Buy&Hold Returns'], name='Buy & Hold'), row=2, col=1)
    
    # Indicator chart
    if indicator == 'SMA Crossover':
        fig.add_trace(go.Scatter(x=data.index, y=data['FastSMA'], name='Fast SMA'), row=3, col=1)
        fig.add_trace(go.Scatter(x=data.index, y=data['SlowSMA'], name='Slow SMA'), row=3, col=1)
    elif indicator == 'MACD':
        fig.add_trace(go.Scatter(x=data.index, y=data['MACD'], name='MACD'), row=3, col=1)
        fig.add_trace(go.Scatter(x=data.index, y=data['Signal'], name='Signal'), row=3, col=1)
    elif indicator == 'RSI':
        fig.add_trace(go.Scatter(x=data.index, y=data['RSI'], name='RSI'), row=3, col=1)
        fig.add_hline(y=overbought, line_dash="dash", row=3, col=1)
        fig.add_hline(y=oversold, line_dash="dash", row=3, col=1)
    elif indicator == 'ATR':
        fig.add_trace(go.Scatter(x=data.index, y=data['Close'], name='Close'), row=3, col=1)
        fig.add_trace(go.Scatter(x=data.index, y=data['UpperBand'], name='Upper Band'), row=3, col=1)
        fig.add_trace(go.Scatter(x=data.index, y=data['LowerBand'], name='Lower Band'), row=3, col=1)
    
    fig.update_layout(height=800, title_text=f"{ticker} Stock Analysis")
    return fig

fig = create_plot(data)
st.plotly_chart(fig, use_container_width=True)

# Display trade details
st.subheader('Trade Details')
st.dataframe(trades[['Type', 'Price', 'Profit/Loss', 'Cumulative P/L']])

# Calculate and display metrics
def calculate_metrics(data):
    total_return = data['Cumulative Returns'].iloc[-1] - 1
    buy_hold_return = data['Buy&Hold Returns'].iloc[-1] - 1
    cagr = (data['Cumulative Returns'].iloc[-1] ** (252 / len(data)) - 1)
    buy_hold_cagr = (data['Buy&Hold Returns'].iloc[-1] ** (252 / len(data)) - 1)
    mdd = (data['Cumulative Returns'] / data['Cumulative Returns'].cummax() - 1).min()
    buy_hold_mdd = (data['Buy&Hold Returns'] / data['Buy&Hold Returns'].cummax() - 1).min()
    max_loss = data['Strategy Returns'].min()
    win_rate = len(data[data['Strategy Returns'] > 0]) / len(data[data['Strategy Returns'] != 0])
    
    metrics = pd.DataFrame({
        'Metric': ['Total Return', 'CAGR', 'Max Drawdown', 'Max Loss', 'Win Rate'],
        'Strategy': [total_return, cagr, mdd, max_loss, win_rate],
        'Buy & Hold': [buy_hold_return, buy_hold_cagr, buy_hold_mdd, data['Returns'].min(), np.nan]
    })
    
    return metrics

metrics = calculate_metrics(data)
st.subheader('Performance Metrics')
st.dataframe(metrics.style.format({'Strategy': '{:.2%}', 'Buy & Hold': '{:.2%}'}))
