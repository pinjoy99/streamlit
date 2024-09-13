import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import talib

# Define the list of top 20 most traded stocks and ETFs
top_tickers = [
    "SPY", "QQQ", "IWM", "EEM", "VTI", "GLD", "XLF", "VEA", "VWO", "IEFA",
    "LQD", "TLT", "HYG", "XLE", "VNQ", "VCIT", "BND", "VGK", "EFA", "AGG"
]

# Sidebar inputs
st.sidebar.header("Settings")
ticker = st.sidebar.selectbox("Select a ticker", top_tickers)
end_date = datetime.now().date()
start_date = st.sidebar.date_input("Start Date", end_date - timedelta(days=4*365))
end_date = st.sidebar.date_input("End Date", end_date)

# Technical indicator selection
indicator = st.sidebar.selectbox("Select an indicator", ["MACD", "RSI", "ATR"])

# Indicator parameters
if indicator == "MACD":
    fast_period = st.sidebar.slider("Fast period", 5, 30, 12)
    slow_period = st.sidebar.slider("Slow period", 10, 50, 26)
    signal_period = st.sidebar.slider("Signal period", 5, 20, 9)
elif indicator == "RSI":
    rsi_period = st.sidebar.slider("RSI period", 5, 30, 14)
    oversold = st.sidebar.slider("Oversold level", 10, 40, 30)
    overbought = st.sidebar.slider("Overbought level", 60, 90, 70)
elif indicator == "ATR":
    atr_period = st.sidebar.slider("ATR period", 5, 30, 14)
    atr_multiplier = st.sidebar.slider("ATR multiplier", 1.0, 5.0, 2.0, 0.1)

# Download historical data
@st.cache_data
def get_data(ticker, start_date, end_date):
    data = yf.download(ticker, start=start_date, end=end_date)
    return data

data = get_data(ticker, start_date, end_date)

# Calculate indicators and signals
if indicator == "MACD":
    macd, signal, _ = talib.MACD(data['Close'], fastperiod=fast_period, slowperiod=slow_period, signalperiod=signal_period)
    buy_signal = (macd > signal) & (macd.shift(1) <= signal.shift(1))
    sell_signal = (macd < signal) & (macd.shift(1) >= signal.shift(1))
    indicator_data = pd.DataFrame({'MACD': macd, 'Signal': signal})
elif indicator == "RSI":
    rsi = talib.RSI(data['Close'], timeperiod=rsi_period)
    buy_signal = (rsi < oversold) & (rsi.shift(1) >= oversold)
    sell_signal = (rsi > overbought) & (rsi.shift(1) <= overbought)
    indicator_data = pd.DataFrame({'RSI': rsi})
elif indicator == "ATR":
    atr = talib.ATR(data['High'], data['Low'], data['Close'], timeperiod=atr_period)
    upper_band = data['Close'] + atr * atr_multiplier
    lower_band = data['Close'] - atr * atr_multiplier
    buy_signal = (data['Close'] > upper_band) & (data['Close'].shift(1) <= upper_band.shift(1))
    sell_signal = (data['Close'] < lower_band) & (data['Close'].shift(1) >= lower_band.shift(1))
    indicator_data = pd.DataFrame({'ATR': atr, 'Upper': upper_band, 'Lower': lower_band})

# Backtest strategy
position = 0
trades = []
for i in range(len(data)):
    if buy_signal.iloc[i] and position == 0:
        position = 1
        entry_price = data['Close'].iloc[i]
        entry_date = data.index[i]
    elif sell_signal.iloc[i] and position == 1:
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

trades_df = pd.DataFrame(trades)
trades_df['Cumulative Profit'] = (1 + trades_df['Profit']).cumprod() - 1

# Calculate buy-and-hold returns
buy_hold_return = (data['Close'].iloc[-1] - data['Close'].iloc[0]) / data['Close'].iloc[0]

# Create interactive plot
fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.05,
                    subplot_titles=('Stock Price', 'Cumulative Profit', indicator))

# Stock price subplot
fig.add_trace(go.Scatter(x=data.index, y=data['Close'], name='Close Price'), row=1, col=1)
fig.add_trace(go.Scatter(x=trades_df['Entry Date'], y=trades_df['Entry Price'], mode='markers', 
                         name='Buy', marker=dict(symbol='triangle-up', size=10, color='green')), row=1, col=1)
fig.add_trace(go.Scatter(x=trades_df['Exit Date'], y=trades_df['Exit Price'], mode='markers', 
                         name='Sell', marker=dict(symbol='triangle-down', size=10, color='red')), row=1, col=1)

# Cumulative profit subplot
fig.add_trace(go.Scatter(x=trades_df['Exit Date'], y=trades_df['Cumulative Profit'], name='Strategy'), row=2, col=1)
fig.add_trace(go.Scatter(x=data.index, y=(data['Close'] - data['Close'].iloc[0]) / data['Close'].iloc[0], 
                         name='Buy and Hold'), row=2, col=1)

# Indicator subplot
if indicator == "MACD":
    fig.add_trace(go.Scatter(x=data.index, y=indicator_data['MACD'], name='MACD'), row=3, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=indicator_data['Signal'], name='Signal'), row=3, col=1)
elif indicator == "RSI":
    fig.add_trace(go.Scatter(x=data.index, y=indicator_data['RSI'], name='RSI'), row=3, col=1)
    fig.add_hline(y=oversold, line_dash="dash", line_color="green", row=3, col=1)
    fig.add_hline(y=overbought, line_dash="dash", line_color="red", row=3, col=1)
elif indicator == "ATR":
    fig.add_trace(go.Scatter(x=data.index, y=indicator_data['ATR'], name='ATR'), row=3, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=indicator_data['Upper'], name='Upper Band'), row=3, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=indicator_data['Lower'], name='Lower Band'), row=3, col=1)

fig.update_layout(height=900, title_text=f"{ticker} Backtest Results")
st.plotly_chart(fig, use_container_width=True)

# Display trade details
st.subheader("Trade Details")
st.dataframe(trades_df)

# Display performance metrics
st.subheader("Performance Metrics")
total_trades = len(trades_df)
winning_trades = len(trades_df[trades_df['Profit'] > 0])
losing_trades = len(trades_df[trades_df['Profit'] <= 0])
win_rate = winning_trades / total_trades if total_trades > 0 else 0
average_profit = trades_df['Profit'].mean() if total_trades > 0 else 0
total_return = trades_df['Cumulative Profit'].iloc[-1] if len(trades_df) > 0 else 0

metrics = pd.DataFrame({
    'Metric': ['Total Trades', 'Winning Trades', 'Losing Trades', 'Win Rate', 'Average Profit', 'Total Return', 'Buy and Hold Return'],
    'Value': [total_trades, winning_trades, losing_trades, f"{win_rate:.2%}", f"{average_profit:.2%}", f"{total_return:.2%}", f"{buy_hold_return:.2%}"]
})

st.table(metrics)
