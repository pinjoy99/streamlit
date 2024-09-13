import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from ta.trend import MACD
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange

# Sidebar inputs
st.sidebar.header("Stock Selection")
ticker = st.sidebar.text_input("Enter stock ticker", value="AAPL")
start_date = st.sidebar.date_input("Start date")
end_date = st.sidebar.date_input("End date")

st.sidebar.header("Strategy Parameters")
indicator = st.sidebar.selectbox("Select indicator", ["MACD", "RSI", "ATR"])

if indicator == "MACD":
    fast_period = st.sidebar.slider("Fast period", 5, 50, 12)
    slow_period = st.sidebar.slider("Slow period", 10, 100, 26)
    signal_period = st.sidebar.slider("Signal period", 5, 20, 9)
elif indicator == "RSI":
    rsi_period = st.sidebar.slider("RSI period", 5, 30, 14)
    oversold = st.sidebar.slider("Oversold threshold", 10, 40, 30)
    overbought = st.sidebar.slider("Overbought threshold", 60, 90, 70)
elif indicator == "ATR":
    atr_period = st.sidebar.slider("ATR period", 5, 30, 14)
    atr_multiplier = st.sidebar.slider("ATR multiplier", 1.0, 5.0, 2.0, 0.1)

# Download data
@st.cache_data
def download_data(ticker, start_date, end_date):
    data = yf.download(ticker, start=start_date, end=end_date)
    return data

data = download_data(ticker, start_date, end_date)

# Calculate indicators and generate signals
def calculate_signals(data, indicator):
    if indicator == "MACD":
        macd = MACD(data['Close'], fast_period, slow_period, signal_period)
        data['MACD'] = macd.macd()
        data['Signal'] = macd.macd_signal()
        data['Buy'] = (data['MACD'] > data['Signal']) & (data['MACD'].shift(1) <= data['Signal'].shift(1))
        data['Sell'] = (data['MACD'] < data['Signal']) & (data['MACD'].shift(1) >= data['Signal'].shift(1))
    elif indicator == "RSI":
        rsi = RSIIndicator(data['Close'], rsi_period)
        data['RSI'] = rsi.rsi()
        data['Buy'] = (data['RSI'] < oversold) & (data['RSI'].shift(1) >= oversold)
        data['Sell'] = (data['RSI'] > overbought) & (data['RSI'].shift(1) <= overbought)
    elif indicator == "ATR":
        atr = AverageTrueRange(data['High'], data['Low'], data['Close'], atr_period)
        data['ATR'] = atr.average_true_range()
        data['Upper'] = data['Close'] + atr_multiplier * data['ATR']
        data['Lower'] = data['Close'] - atr_multiplier * data['ATR']
        data['Buy'] = (data['Close'] > data['Upper']) & (data['Close'].shift(1) <= data['Upper'].shift(1))
        data['Sell'] = (data['Close'] < data['Lower']) & (data['Close'].shift(1) >= data['Lower'].shift(1))
    return data

data = calculate_signals(data, indicator)

# Backtest strategy
def backtest_strategy(data):
    data['Position'] = np.nan
    data.loc[data['Buy'], 'Position'] = 1
    data.loc[data['Sell'], 'Position'] = 0
    data['Position'] = data['Position'].ffill().fillna(0)
    data['Returns'] = data['Close'].pct_change()
    data['Strategy_Returns'] = data['Position'].shift(1) * data['Returns']
    data['Cumulative_Returns'] = (1 + data['Strategy_Returns']).cumprod()
    data['Drawdown'] = (data['Cumulative_Returns'].cummax() - data['Cumulative_Returns']) / data['Cumulative_Returns'].cummax()
    return data

data = backtest_strategy(data)

# Create subplots
fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.05, subplot_titles=("Stock Price", "Profit/Loss", f"{indicator} Indicator"))

# Stock price chart
fig.add_trace(go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'], name="Price"), row=1, col=1)
fig.add_trace(go.Scatter(x=data.index[data['Buy']], y=data.loc[data['Buy'], 'Close'], mode='markers', marker=dict(symbol='triangle-up', size=10, color='green'), name='Buy Signal'), row=1, col=1)
fig.add_trace(go.Scatter(x=data.index[data['Sell']], y=data.loc[data['Sell'], 'Close'], mode='markers', marker=dict(symbol='triangle-down', size=10, color='red'), name='Sell Signal'), row=1, col=1)

# Profit/Loss chart
fig.add_trace(go.Scatter(x=data.index, y=data['Cumulative_Returns'], name="Cumulative Returns"), row=2, col=1)

# Indicator chart
if indicator == "MACD":
    fig.add_trace(go.Scatter(x=data.index, y=data['MACD'], name="MACD"), row=3, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data['Signal'], name="Signal"), row=3, col=1)
elif indicator == "RSI":
    fig.add_trace(go.Scatter(x=data.index, y=data['RSI'], name="RSI"), row=3, col=1)
    fig.add_hline(y=oversold, line_dash="dash", line_color="green", row=3, col=1)
    fig.add_hline(y=overbought, line_dash="dash", line_color="red", row=3, col=1)
elif indicator == "ATR":
    fig.add_trace(go.Scatter(x=data.index, y=data['Upper'], name="Upper Band"), row=3, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data['Lower'], name="Lower Band"), row=3, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'], name="Close Price"), row=3, col=1)

fig.update_layout(height=900, title_text=f"Backtest Results for {ticker}")
st.plotly_chart(fig, use_container_width=True)

# Trade details table
trades = data[data['Position'] != data['Position'].shift(1)].copy()
trades['Trade_Type'] = np.where(trades['Position'] == 1, 'Buy', 'Sell')
trades['Price'] = trades['Close']
trades['Profit/Loss'] = trades['Close'].diff()
trades['Cumulative_Profit/Loss'] = trades['Profit/Loss'].cumsum()

st.subheader("Trade Details")
st.dataframe(trades[['Trade_Type', 'Price', 'Profit/Loss', 'Cumulative_Profit/Loss']])

# Performance metrics
total_return = data['Cumulative_Returns'].iloc[-1] - 1
sharpe_ratio = data['Strategy_Returns'].mean() / data['Strategy_Returns'].std() * np.sqrt(252)
max_drawdown = data['Drawdown'].max()

st.subheader("Performance Metrics")
col1, col2, col3 = st.columns(3)
col1.metric("Total Return", f"{total_return:.2%}")
col2.metric("Sharpe Ratio", f"{sharpe_ratio:.2f}")
col3.metric("Max Drawdown", f"{max_drawdown:.2%}")
