import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from ta.trend import SMAIndicator, MACD
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange

# Function to download stock data
def get_stock_data(ticker, start_date, end_date):
    return yf.download(ticker, start=start_date, end=end_date)

# Function to calculate indicators
def calculate_indicators(data, indicator, params):
    if indicator == 'SMA Crossover':
        short_sma = SMAIndicator(data['Close'], window=params['short_window']).sma_indicator()
        long_sma = SMAIndicator(data['Close'], window=params['long_window']).sma_indicator()
        data['Signal'] = np.where(short_sma > long_sma, 1, 0)
    elif indicator == 'MACD':
        macd = MACD(data['Close']).macd()
        signal = MACD(data['Close']).macd_signal()
        data['Signal'] = np.where(macd > signal, 1, 0)
    elif indicator == 'RSI':
        rsi = RSIIndicator(data['Close']).rsi()
        data['Signal'] = np.where(rsi < params['oversold'], 1, np.where(rsi > params['overbought'], 0, np.nan))
        data['Signal'] = data['Signal'].ffill()
    elif indicator == 'ATR':
        atr = AverageTrueRange(data['High'], data['Low'], data['Close']).average_true_range()
        data['Signal'] = np.where(atr > params['threshold'], 1, 0)
    return data

# Function to backtest strategy
def backtest_strategy(data):
    data['Position'] = data['Signal'].shift(1)
    data['Returns'] = data['Close'].pct_change()
    data['Strategy_Returns'] = data['Position'] * data['Returns']
    data['Cumulative_Returns'] = (1 + data['Strategy_Returns']).cumprod()
    data['Buy_and_Hold_Returns'] = (1 + data['Returns']).cumprod()
    return data

# Function to calculate performance metrics
def calculate_metrics(data):
    total_return = data['Cumulative_Returns'].iloc[-1] - 1
    bnh_return = data['Buy_and_Hold_Returns'].iloc[-1] - 1
    cagr = (data['Cumulative_Returns'].iloc[-1] ** (252 / len(data)) - 1)
    mdd = (data['Cumulative_Returns'] / data['Cumulative_Returns'].cummax() - 1).min()
    win_rate = (data['Strategy_Returns'] > 0).mean()
    return {
        'Total Return': f'{total_return:.2%}',
        'Buy & Hold Return': f'{bnh_return:.2%}',
        'CAGR': f'{cagr:.2%}',
        'Max Drawdown': f'{mdd:.2%}',
        'Win Rate': f'{win_rate:.2%}'
    }

# Streamlit app
st.title('Stock Trading Strategy Backtester')

# Sidebar
st.sidebar.header('Input Parameters')
ticker = st.sidebar.selectbox('Select Stock', ['AAPL', 'MSFT', 'AMZN', 'GOOGL', 'FB', 'TSLA', 'NVDA', 'JPM', 'JNJ', 'V'])
start_date = st.sidebar.date_input('Start Date', pd.to_datetime('2020-01-01'))
end_date = st.sidebar.date_input('End Date', pd.to_datetime('today'))

indicator = st.sidebar.selectbox('Select Indicator', ['SMA Crossover', 'MACD', 'RSI', 'ATR'])

if indicator == 'SMA Crossover':
    short_window = st.sidebar.slider('Short Window', 5, 50, 20)
    long_window = st.sidebar.slider('Long Window', 20, 200, 50)
    params = {'short_window': short_window, 'long_window': long_window}
elif indicator == 'RSI':
    oversold = st.sidebar.slider('Oversold Level', 20, 40, 30)
    overbought = st.sidebar.slider('Overbought Level', 60, 80, 70)
    params = {'oversold': oversold, 'overbought': overbought}
elif indicator == 'ATR':
    threshold = st.sidebar.slider('ATR Threshold', 0.5, 5.0, 2.0, 0.1)
    params = {'threshold': threshold}
else:
    params = {}

# Main app
data = get_stock_data(ticker, start_date, end_date)
data = calculate_indicators(data, indicator, params)
data = backtest_strategy(data)

# Plot
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 16), sharex=True)

ax1.plot(data.index, data['Close'], label='Close Price')
ax1.plot(data[data['Signal'] == 1].index, data['Close'][data['Signal'] == 1], '^', markersize=10, color='g', label='Buy Signal')
ax1.plot(data[data['Signal'] == 0].index, data['Close'][data['Signal'] == 0], 'v', markersize=10, color='r', label='Sell Signal')
ax1.set_title('Stock Price and Signals')
ax1.legend()

ax2.plot(data.index, data['Cumulative_Returns'], label='Strategy Returns')
ax2.plot(data.index, data['Buy_and_Hold_Returns'], label='Buy and Hold Returns')
ax2.set_title('Cumulative Returns')
ax2.legend()

if indicator == 'SMA Crossover':
    ax3.plot(data.index, data['SMA_20'], label='Short SMA')
    ax3.plot(data.index, data['SMA_50'], label='Long SMA')
elif indicator == 'MACD':
    ax3.plot(data.index, data['MACD'], label='MACD')
    ax3.plot(data.index, data['MACD_signal'], label='Signal Line')
elif indicator == 'RSI':
    ax3.plot(data.index, data['RSI'], label='RSI')
    ax3.axhline(y=oversold, color='g', linestyle='--')
    ax3.axhline(y=overbought, color='r', linestyle='--')
elif indicator == 'ATR':
    ax3.plot(data.index, data['ATR'], label='ATR')
    ax3.axhline(y=threshold, color='r', linestyle='--')

ax3.set_title(f'{indicator} Indicator')
ax3.legend()

st.pyplot(fig)

# Performance metrics
metrics = calculate_metrics(data)
st.subheader('Performance Metrics')
st.write(pd.DataFrame([metrics]))

# Trade details
st.subheader('Trade Details')
trades = data[data['Signal'] != data['Signal'].shift(1)].copy()
trades['Holding_Period'] = (trades.index - trades.index.shift(1)).days
trades['Profit/Loss'] = trades['Close'] * trades['Position'].shift(1) * (trades['Returns'] + 1)
trades['Cumulative_Profit/Loss'] = trades['Profit/Loss'].cumsum()
st.write(trades[['Close', 'Signal', 'Holding_Period', 'Profit/Loss', 'Cumulative_Profit/Loss']])

# Download data
st.download_button(
    label="Download Data as CSV",
    data=data.to_csv().encode('utf-8'),
    file_name=f'{ticker}_backtest_data.csv',
    mime='text/csv',
)
