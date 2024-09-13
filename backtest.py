import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import ta

# Define the list of top 20 most traded stocks and ETFs
top_tickers = [
    "SPY", "QQQ", "IWM", "VXUS", "RSP", "EEM", "SHV", "XLF", "SPDR", "IVV",
    "EFA", "TLT", "XLV", "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA"
]

# Sidebar inputs
st.sidebar.header("Settings")
ticker = st.sidebar.selectbox("Select a stock/ETF", top_tickers)
end_date = datetime.now()
start_date = st.sidebar.date_input("Start Date", end_date - timedelta(days=5*365))
end_date = st.sidebar.date_input("End Date", end_date)

# Technical indicator selection
indicator = st.sidebar.selectbox("Select an indicator", ["MACD", "RSI", "ATR"])

# Indicator parameters
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
def get_data(ticker, start_date, end_date):
    data = yf.download(ticker, start=start_date, end=end_date)
    return data

data = get_data(ticker, start_date, end_date)

# Calculate indicators
def calculate_indicator(data, indicator):
    if indicator == "MACD":
        macd = ta.trend.MACD(data['Close'], fast_period, slow_period, signal_period)
        data['MACD'] = macd.macd()
        data['Signal'] = macd.macd_signal()
        data['MACD_Hist'] = macd.macd_diff()
        data['Buy_Signal'] = (data['MACD'] > data['Signal']) & (data['MACD'].shift(1) <= data['Signal'].shift(1))
        data['Sell_Signal'] = (data['MACD'] < data['Signal']) & (data['MACD'].shift(1) >= data['Signal'].shift(1))
    elif indicator == "RSI":
        data['RSI'] = ta.momentum.RSIIndicator(data['Close'], rsi_period).rsi()
        data['Buy_Signal'] = (data['RSI'] < oversold) & (data['RSI'].shift(1) >= oversold)
        data['Sell_Signal'] = (data['RSI'] > overbought) & (data['RSI'].shift(1) <= overbought)
    elif indicator == "ATR":
        atr = ta.volatility.AverageTrueRange(data['High'], data['Low'], data['Close'], atr_period).average_true_range()
        data['Upper_Band'] = data['Close'] + atr * atr_multiplier
        data['Lower_Band'] = data['Close'] - atr * atr_multiplier
        data['Buy_Signal'] = (data['Close'] > data['Upper_Band']) & (data['Close'].shift(1) <= data['Upper_Band'].shift(1))
        data['Sell_Signal'] = (data['Close'] < data['Lower_Band']) & (data['Close'].shift(1) >= data['Lower_Band'].shift(1))
    return data

data = calculate_indicator(data, indicator)

# Backtesting
def backtest(data):
    position = 0
    trades = []
    for i in range(len(data)):
        if data['Buy_Signal'].iloc[i] and position == 0:
            position = 1
            entry_price = data['Close'].iloc[i]
            entry_date = data.index[i]
        elif data['Sell_Signal'].iloc[i] and position == 1:
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
    
    strategy_returns = data['Close'].pct_change()
    strategy_returns[data['Buy_Signal']] = 0
    strategy_returns = (1 + strategy_returns).cumprod() - 1
    
    buy_and_hold_returns = (data['Close'] / data['Close'].iloc[0]) - 1
    
    return trades_df, strategy_returns, buy_and_hold_returns

trades_df, strategy_returns, buy_and_hold_returns = backtest(data)

# Plotting
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 16), sharex=True)

# Price chart
ax1.plot(data.index, data['Close'], label='Close Price')
ax1.set_title(f"{ticker} Price Chart")
ax1.legend()

# Profit/Loss chart
ax2.plot(strategy_returns.index, strategy_returns, label='Strategy Returns')
ax2.plot(buy_and_hold_returns.index, buy_and_hold_returns, label='Buy and Hold Returns')
ax2.set_title("Profit/Loss Chart")
ax2.legend()

# Indicator chart
if indicator == "MACD":
    ax3.plot(data.index, data['MACD'], label='MACD')
    ax3.plot(data.index, data['Signal'], label='Signal')
    ax3.bar(data.index, data['MACD_Hist'], label='MACD Histogram')
elif indicator == "RSI":
    ax3.plot(data.index, data['RSI'], label='RSI')
    ax3.axhline(y=overbought, color='r', linestyle='--')
    ax3.axhline(y=oversold, color='g', linestyle='--')
elif indicator == "ATR":
    ax3.plot(data.index, data['Upper_Band'], label='Upper Band')
    ax3.plot(data.index, data['Lower_Band'], label='Lower Band')
    ax3.plot(data.index, data['Close'], label='Close Price')

ax3.set_title(f"{indicator} Chart")
ax3.legend()

# Plot buy/sell signals
buy_signals = data[data['Buy_Signal']]
sell_signals = data[data['Sell_Signal']]
ax1.scatter(buy_signals.index, buy_signals['Close'], color='green', marker='^', s=100)
ax1.scatter(sell_signals.index, sell_signals['Close'], color='red', marker='v', s=100)

st.pyplot(fig)

# Display trade details
st.subheader("Trade Details")
st.dataframe(trades_df)

# Display summary statistics
st.subheader("Summary Statistics")
total_trades = len(trades_df)
profitable_trades = len(trades_df[trades_df['Profit'] > 0])
loss_making_trades = len(trades_df[trades_df['Profit'] < 0])
win_rate = profitable_trades / total_trades if total_trades > 0 else 0
average_profit = trades_df['Profit'].mean() if total_trades > 0 else 0
total_return = trades_df['Cumulative Profit'].iloc[-1] if total_trades > 0 else 0

st.write(f"Total Trades: {total_trades}")
st.write(f"Profitable Trades: {profitable_trades}")
st.write(f"Loss-making Trades: {loss_making_trades}")
st.write(f"Win Rate: {win_rate:.2%}")
st.write(f"Average Profit per Trade: {average_profit:.2%}")
st.write(f"Total Return: {total_return:.2%}")
