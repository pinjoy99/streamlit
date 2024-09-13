import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import talib

# Set page config
st.set_page_config(layout="wide", page_title="Stock Trading Strategy Backtester")

# Sidebar inputs
st.sidebar.title("Stock Trading Strategy Backtester")

# List of top 20 most traded stocks and ETFs
tickers = ['AAPL', 'MSFT', 'AMZN', 'GOOGL', 'FB', 'TSLA', 'NVDA', 'JPM', 'JNJ', 'V', 'PG', 'UNH', 'HD', 'BAC', 'MA', 'DIS', 'ADBE', 'CRM', 'NFLX', 'SPY']

# Stock selection
selected_ticker = st.sidebar.selectbox("Select a stock", tickers)

# Date range selection
end_date = datetime.now().date()
start_date = end_date - timedelta(days=4*365)  # Default to 4 years
start_date = st.sidebar.date_input("Start date", start_date)
end_date = st.sidebar.date_input("End date", end_date)

# Strategy selection
strategy = st.sidebar.selectbox("Select a strategy", ["MACD", "RSI", "ATR"])

# Strategy parameters
if strategy == "MACD":
    fast_period = st.sidebar.slider("Fast period", 5, 50, 12)
    slow_period = st.sidebar.slider("Slow period", 10, 100, 26)
    signal_period = st.sidebar.slider("Signal period", 5, 20, 9)
elif strategy == "RSI":
    rsi_period = st.sidebar.slider("RSI period", 5, 30, 14)
    oversold = st.sidebar.slider("Oversold threshold", 10, 40, 30)
    overbought = st.sidebar.slider("Overbought threshold", 60, 90, 70)
elif strategy == "ATR":
    atr_period = st.sidebar.slider("ATR period", 5, 30, 14)
    atr_multiplier = st.sidebar.slider("ATR multiplier", 1.0, 5.0, 2.0, 0.1)

# Download data
@st.cache_data
def download_data(ticker, start, end):
    data = yf.download(ticker, start, end)
    return data

data = download_data(selected_ticker, start_date, end_date)

# Calculate indicators and generate signals
def calculate_signals(data, strategy):
    if strategy == "MACD":
        data['MACD'], data['Signal'], _ = talib.MACD(data['Close'], fastperiod=fast_period, slowperiod=slow_period, signalperiod=signal_period)
        data['Signal'] = np.where((data['MACD'] > data['Signal']) & (data['MACD'].shift(1) <= data['Signal'].shift(1)), 1, 0)  # Buy signal
        data['Signal'] = np.where((data['MACD'] < data['Signal']) & (data['MACD'].shift(1) >= data['Signal'].shift(1)), -1, data['Signal'])  # Sell signal
    elif strategy == "RSI":
        data['RSI'] = talib.RSI(data['Close'], timeperiod=rsi_period)
        data['Signal'] = np.where((data['RSI'] < oversold) & (data['RSI'].shift(1) >= oversold), 1, 0)  # Buy signal
        data['Signal'] = np.where((data['RSI'] > overbought) & (data['RSI'].shift(1) <= overbought), -1, data['Signal'])  # Sell signal
    elif strategy == "ATR":
        data['ATR'] = talib.ATR(data['High'], data['Low'], data['Close'], timeperiod=atr_period)
        data['Upper'] = data['Close'] + atr_multiplier * data['ATR']
        data['Lower'] = data['Close'] - atr_multiplier * data['ATR']
        data['Signal'] = np.where(data['Close'] > data['Upper'].shift(1), 1, 0)  # Buy signal
        data['Signal'] = np.where(data['Close'] < data['Lower'].shift(1), -1, data['Signal'])  # Sell signal
    return data

data = calculate_signals(data, strategy)

# Backtesting
def backtest(data):
    position = 0
    trades = []
    for i in range(1, len(data)):
        if data['Signal'].iloc[i] == 1 and position == 0:
            position = 1
            entry_price = data['Close'].iloc[i]
            entry_date = data.index[i]
        elif (data['Signal'].iloc[i] == -1 or i == len(data) - 1) and position == 1:
            position = 0
            exit_price = data['Close'].iloc[i]
            exit_date = data.index[i]
            trades.append({
                'Entry Date': entry_date,
                'Entry Price': entry_price,
                'Exit Date': exit_date,
                'Exit Price': exit_price,
                'Profit': (exit_price - entry_price) / entry_price
            })
    return pd.DataFrame(trades)

trades = backtest(data)

# Calculate cumulative returns
data['Strategy'] = (1 + trades['Profit']).cumprod()
data['Buy&Hold'] = data['Close'] / data['Close'].iloc[0]

# Plotting
fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.5, 0.3, 0.2])

# Stock price chart with buy/sell markers
fig.add_trace(go.Scatter(x=data.index, y=data['Close'], name='Stock Price'), row=1, col=1)
fig.add_trace(go.Scatter(x=trades['Entry Date'], y=data.loc[trades['Entry Date'], 'Close'], mode='markers', marker=dict(symbol='triangle-up', size=10, color='green'), name='Buy'), row=1, col=1)
fig.add_trace(go.Scatter(x=trades['Exit Date'], y=data.loc[trades['Exit Date'], 'Close'], mode='markers', marker=dict(symbol='triangle-down', size=10, color='red'), name='Sell'), row=1, col=1)

# Cumulative returns chart
fig.add_trace(go.Scatter(x=data.index, y=data['Strategy'], name='Strategy Returns'), row=2, col=1)
fig.add_trace(go.Scatter(x=data.index, y=data['Buy&Hold'], name='Buy & Hold Returns'), row=2, col=1)

# Indicator chart
if strategy == "MACD":
    fig.add_trace(go.Scatter(x=data.index, y=data['MACD'], name='MACD'), row=3, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data['Signal'], name='Signal Line'), row=3, col=1)
elif strategy == "RSI":
    fig.add_trace(go.Scatter(x=data.index, y=data['RSI'], name='RSI'), row=3, col=1)
    fig.add_hline(y=oversold, line_dash="dash", line_color="green", row=3, col=1)
    fig.add_hline(y=overbought, line_dash="dash", line_color="red", row=3, col=1)
elif strategy == "ATR":
    fig.add_trace(go.Scatter(x=data.index, y=data['Upper'], name='Upper Band'), row=3, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data['Lower'], name='Lower Band'), row=3, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'], name='Close Price'), row=3, col=1)

fig.update_layout(height=800, title_text=f"{selected_ticker} - {strategy} Strategy Backtest")
st.plotly_chart(fig, use_container_width=True)

# Trade details table
st.subheader("Trade Details")
trades['Realized Gain/Loss'] = (trades['Exit Price'] - trades['Entry Price']) * 100
trades['Cumulative Gain/Loss'] = trades['Realized Gain/Loss'].cumsum()
st.dataframe(trades)

# Performance metrics
total_return = (data['Strategy'].iloc[-1] - 1) * 100
buy_hold_return = (data['Buy&Hold'].iloc[-1] - 1) * 100
st.subheader("Performance Metrics")
col1, col2 = st.columns(2)
col1.metric("Total Return", f"{total_return:.2f}%")
col2.metric("Buy & Hold Return", f"{buy_hold_return:.2f}%")
