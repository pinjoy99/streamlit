import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import ta

st.set_page_config(layout="wide")

st.title("Stock Trading Strategy Backtester")

# Sidebar inputs
st.sidebar.header("Settings")

# Top 20 most traded stocks and ETFs
top_tickers = ["NVDA", "TSLA", "AAPL", "MSFT", "NU", "AMD", "META", "AMZN", "QCOM", "JPM", 
               "LULU", "CRWD", "MU", "WMT", "ULTA", "SPY", "QQQ", "IWM", "DIA", "XLF"]

ticker = st.sidebar.selectbox("Select Stock/ETF", top_tickers)

end_date = datetime.now()
start_date = end_date - timedelta(days=4*365)

date_range = st.sidebar.date_input("Date Range", [start_date, end_date])

indicators = ["MACD", "RSI", "ATR"]
selected_indicator = st.sidebar.selectbox("Select Indicator", indicators)

if selected_indicator == "MACD":
    fast_period = st.sidebar.slider("Fast Period", 5, 50, 12)
    slow_period = st.sidebar.slider("Slow Period", 10, 100, 26)
    signal_period = st.sidebar.slider("Signal Period", 5, 20, 9)
elif selected_indicator == "RSI":
    rsi_period = st.sidebar.slider("RSI Period", 5, 30, 14)
    overbought = st.sidebar.slider("Overbought Level", 60, 90, 70)
    oversold = st.sidebar.slider("Oversold Level", 10, 40, 30)
elif selected_indicator == "ATR":
    atr_period = st.sidebar.slider("ATR Period", 5, 30, 14)
    atr_multiplier = st.sidebar.slider("ATR Multiplier", 1.0, 5.0, 2.0, 0.1)

# Download data
@st.cache_data
def download_data(ticker, start_date, end_date):
    data = yf.download(ticker, start=start_date, end=end_date)
    return data

data = download_data(ticker, date_range[0], date_range[1])

# Calculate indicators and signals
def calculate_signals(data, indicator):
    if indicator == "MACD":
        macd = ta.trend.MACD(data['Close'], fast_period, slow_period, signal_period)
        data['MACD'] = macd.macd()
        data['Signal'] = macd.macd_signal()
        data['Buy'] = (data['MACD'] > data['Signal']) & (data['MACD'].shift(1) <= data['Signal'].shift(1))
        data['Sell'] = (data['MACD'] < data['Signal']) & (data['MACD'].shift(1) >= data['Signal'].shift(1))
    elif indicator == "RSI":
        data['RSI'] = ta.momentum.RSIIndicator(data['Close'], rsi_period).rsi()
        data['Buy'] = (data['RSI'] < oversold) & (data['RSI'].shift(1) >= oversold)
        data['Sell'] = (data['RSI'] > overbought) & (data['RSI'].shift(1) <= overbought)
    elif indicator == "ATR":
        atr = ta.volatility.AverageTrueRange(data['High'], data['Low'], data['Close'], atr_period).average_true_range()
        data['Upper'] = data['Close'] + atr_multiplier * atr
        data['Lower'] = data['Close'] - atr_multiplier * atr
        data['Buy'] = (data['Close'] < data['Lower']) & (data['Close'].shift(1) >= data['Lower'].shift(1))
        data['Sell'] = (data['Close'] > data['Upper']) & (data['Close'].shift(1) <= data['Upper'].shift(1))
    return data

data = calculate_signals(data, selected_indicator)

# Backtesting
def backtest(data):
    position = 0
    trades = []
    for i in range(len(data)):
        if data['Buy'].iloc[i] and position == 0:
            position = 1
            entry_price = data['Close'].iloc[i]
            entry_date = data.index[i]
        elif data['Sell'].iloc[i] and position == 1:
            position = 0
            exit_price = data['Close'].iloc[i]
            exit_date = data.index[i]
            profit = (exit_price - entry_price) / entry_price
            trades.append({
                'Entry Date': entry_date,
                'Entry Price': entry_price,
                'Exit Date': exit_date,
                'Exit Price': exit_price,
                'Profit': profit
            })
    return pd.DataFrame(trades)

trades = backtest(data)

# Calculate cumulative returns
data['Strategy'] = 1.0
for i, trade in trades.iterrows():
    mask = (data.index >= trade['Entry Date']) & (data.index <= trade['Exit Date'])
    data.loc[mask, 'Strategy'] *= (1 + trade['Profit'])

data['Buy_and_Hold'] = data['Close'] / data['Close'].iloc[0]

# Plotting
fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.05, 
                    subplot_titles=('Price', 'Cumulative Returns', selected_indicator))

fig.add_trace(go.Scatter(x=data.index, y=data['Close'], name='Close Price'), row=1, col=1)
fig.add_trace(go.Scatter(x=trades['Entry Date'], y=trades['Entry Price'], mode='markers', 
                         name='Buy', marker=dict(symbol='triangle-up', size=10, color='green')), row=1, col=1)
fig.add_trace(go.Scatter(x=trades['Exit Date'], y=trades['Exit Price'], mode='markers', 
                         name='Sell', marker=dict(symbol='triangle-down', size=10, color='red')), row=1, col=1)

fig.add_trace(go.Scatter(x=data.index, y=data['Strategy'], name='Strategy'), row=2, col=1)
fig.add_trace(go.Scatter(x=data.index, y=data['Buy_and_Hold'], name='Buy and Hold'), row=2, col=1)

if selected_indicator == "MACD":
    fig.add_trace(go.Scatter(x=data.index, y=data['MACD'], name='MACD'), row=3, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data['Signal'], name='Signal'), row=3, col=1)
elif selected_indicator == "RSI":
    fig.add_trace(go.Scatter(x=data.index, y=data['RSI'], name='RSI'), row=3, col=1)
    fig.add_hline(y=overbought, line_dash="dash", line_color="red", row=3, col=1)
    fig.add_hline(y=oversold, line_dash="dash", line_color="green", row=3, col=1)
elif selected_indicator == "ATR":
    fig.add_trace(go.Scatter(x=data.index, y=data['Upper'], name='Upper Band'), row=3, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data['Lower'], name='Lower Band'), row=3, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'], name='Close Price'), row=3, col=1)

fig.update_layout(height=900, width=1200, title_text=f"{ticker} - {selected_indicator} Strategy Backtest")
st.plotly_chart(fig)

# Trade details table
st.subheader("Trade Details")
trades['Realized Gain/Loss'] = (trades['Exit Price'] - trades['Entry Price']) * 100
trades['Cumulative Gain/Loss'] = trades['Realized Gain/Loss'].cumsum()
st.dataframe(trades)

# Performance metrics
total_return = (data['Strategy'].iloc[-1] - 1) * 100
buy_hold_return = (data['Buy_and_Hold'].iloc[-1] - 1) * 100
st.subheader("Performance Metrics")
col1, col2 = st.columns(2)
col1.metric("Total Return", f"{total_return:.2f}%")
col2.metric("Buy and Hold Return", f"{buy_hold_return:.2f}%")
