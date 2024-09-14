import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from ta.trend import MACD
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange

# Define the list of top 30 most traded stocks and ETFs
top_30 = ['NVDA', 'TSLA', 'TSM', 'SOXL', 'NVDL', 'TQQQ', 'AAPL', 'AMD', 'SMCI', 'MSFT', 
          'SQQQ', 'PLTR', 'TSLL', 'QQQ', 'AVGO', 'SOXS', 'ARM', 'MU', 'VOO', 'AMZN', 
          'CRWD', 'INTC', 'TLT', 'META', 'MARA', 'SPY', 'GOOGL', 'NFLX', 'NVAX', 'BABA']

st.title("Stock Trading Strategy Backtester")

# Sidebar inputs
st.sidebar.header("Settings")
ticker = st.sidebar.selectbox("Select a stock", top_30)
years = st.sidebar.number_input("Number of years of historical data", min_value=1, max_value=10, value=4)
end_date = pd.Timestamp.now()
start_date = end_date - pd.DateOffset(years=years)

indicator = st.sidebar.selectbox("Select an indicator", ["MACD", "RSI", "ATR"])

if indicator == "MACD":
    fast_period = st.sidebar.slider("Fast period", 5, 50, 12)
    slow_period = st.sidebar.slider("Slow period", 10, 100, 26)
    signal_period = st.sidebar.slider("Signal period", 5, 20, 9)
elif indicator == "RSI":
    rsi_period = st.sidebar.slider("RSI period", 5, 30, 14)
    overbought = st.sidebar.slider("Overbought level", 60, 90, 70)
    oversold = st.sidebar.slider("Oversold level", 10, 40, 30)
elif indicator == "ATR":
    atr_period = st.sidebar.slider("ATR period", 5, 30, 14)
    atr_multiplier = st.sidebar.slider("ATR multiplier", 1.0, 5.0, 2.0, 0.1)

# Download data
@st.cache_data
def download_data(ticker, start_date, end_date):
    data = yf.download(ticker, start=start_date, end=end_date)
    return data

data = download_data(ticker, start_date, end_date)

# Calculate indicators
if indicator == "MACD":
    macd = MACD(data['Close'], window_fast=fast_period, window_slow=slow_period, window_sign=signal_period)
    data['MACD'] = macd.macd()
    data['Signal'] = macd.macd_signal()
    data['Buy'] = (data['MACD'] > data['Signal']) & (data['MACD'].shift(1) <= data['Signal'].shift(1))
    data['Sell'] = (data['MACD'] < data['Signal']) & (data['MACD'].shift(1) >= data['Signal'].shift(1))
elif indicator == "RSI":
    rsi = RSIIndicator(data['Close'], window=rsi_period)
    data['RSI'] = rsi.rsi()
    data['Buy'] = (data['RSI'] < oversold) & (data['RSI'].shift(1) >= oversold)
    data['Sell'] = (data['RSI'] > overbought) & (data['RSI'].shift(1) <= overbought)
elif indicator == "ATR":
    atr = AverageTrueRange(data['High'], data['Low'], data['Close'], window=atr_period)
    data['ATR'] = atr.average_true_range()
    data['Upper'] = data['Close'].rolling(window=atr_period).mean() + atr_multiplier * data['ATR']
    data['Lower'] = data['Close'].rolling(window=atr_period).mean() - atr_multiplier * data['ATR']
    data['Buy'] = (data['Close'] > data['Upper']) & (data['Close'].shift(1) <= data['Upper'].shift(1))
    data['Sell'] = (data['Close'] < data['Lower']) & (data['Close'].shift(1) >= data['Lower'].shift(1))

# Backtesting
data['Position'] = np.nan
data.loc[data['Buy'], 'Position'] = 1
data.loc[data['Sell'], 'Position'] = 0
data['Position'] = data['Position'].ffill().fillna(0)
data['Strategy'] = data['Position'].shift(1) * data['Close'].pct_change()
data['Benchmark'] = data['Close'].pct_change()

# Calculate cumulative returns
data['Cum_Strategy'] = (1 + data['Strategy']).cumprod()
data['Cum_Benchmark'] = (1 + data['Benchmark']).cumprod()

# Create interactive plot
fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.05, 
                    subplot_titles=("Stock Price", "Cumulative Returns", f"{indicator} Indicator"))

# Stock price subplot
fig.add_trace(go.Scatter(x=data.index, y=data['Close'], name="Close Price"), row=1, col=1)
fig.add_trace(go.Scatter(x=data[data['Buy']].index, y=data[data['Buy']]['Close'], 
                         mode='markers', name='Buy Signal', marker=dict(color='green', symbol='triangle-up', size=10)), row=1, col=1)
fig.add_trace(go.Scatter(x=data[data['Sell']].index, y=data[data['Sell']]['Close'], 
                         mode='markers', name='Sell Signal', marker=dict(color='red', symbol='triangle-down', size=10)), row=1, col=1)

# Cumulative returns subplot
fig.add_trace(go.Scatter(x=data.index, y=data['Cum_Strategy'], name="Strategy Returns"), row=2, col=1)
fig.add_trace(go.Scatter(x=data.index, y=data['Cum_Benchmark'], name="Buy & Hold Returns"), row=2, col=1)

# Indicator subplot
if indicator == "MACD":
    fig.add_trace(go.Scatter(x=data.index, y=data['MACD'], name="MACD"), row=3, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data['Signal'], name="Signal"), row=3, col=1)
elif indicator == "RSI":
    fig.add_trace(go.Scatter(x=data.index, y=data['RSI'], name="RSI"), row=3, col=1)
    fig.add_hline(y=overbought, line_dash="dash", line_color="red", row=3, col=1)
    fig.add_hline(y=oversold, line_dash="dash", line_color="green", row=3, col=1)
elif indicator == "ATR":
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'], name="Close"), row=3, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data['Upper'], name="Upper Band"), row=3, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data['Lower'], name="Lower Band"), row=3, col=1)

fig.update_layout(height=900, width=800, title_text=f"{ticker} Trading Strategy Backtest")
st.plotly_chart(fig)

# Calculate trade details
trades = data[data['Position'] != data['Position'].shift(1)].copy()
trades['Trade'] = trades['Position'].diff()
trades = trades[trades['Trade'] != 0]
trades['Holding Period'] = trades.index.to_series().diff().dt.days
trades['Profit/Loss'] = trades['Close'] * trades['Trade'] * -1
trades['Cumulative P/L'] = trades['Profit/Loss'].cumsum()

# Display trade details table
st.subheader("Trade Details")
st.dataframe(trades[['Close', 'Trade', 'Holding Period', 'Profit/Loss', 'Cumulative P/L']])

# Display performance metrics
total_trades = len(trades)
profitable_trades = (trades['Profit/Loss'] > 0).sum()
win_rate = profitable_trades / total_trades if total_trades > 0 else 0
average_profit = trades['Profit/Loss'].mean()
total_return = trades['Profit/Loss'].sum()
buy_hold_return = data['Close'].iloc[-1] / data['Close'].iloc[0] - 1

st.subheader("Performance Metrics")
col1, col2, col3 = st.columns(3)
col1.metric("Total Trades", total_trades)
col2.metric("Win Rate", f"{win_rate:.2%}")
col3.metric("Average Profit/Loss", f"${average_profit:.2f}")

col4, col5, col6 = st.columns(3)
col4.metric("Total Return", f"${total_return:.2f}")
col5.metric("Strategy Return", f"{(data['Cum_Strategy'].iloc[-1] - 1):.2%}")
col6.metric("Buy & Hold Return", f"{buy_hold_return:.2%}")
