import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import ta
from datetime import datetime, timedelta

# Define the list of top 20 most traded stocks and ETFs
TOP_TICKERS = ['AAPL', 'MSFT', 'AMZN', 'GOOGL', 'FB', 'TSLA', 'NVDA', 'JPM', 'JNJ', 'V', 'PG', 'UNH', 'HD', 'BAC', 'MA', 'DIS', 'ADBE', 'CRM', 'NFLX', 'SPY']

# Sidebar inputs
st.sidebar.title("Stock Trading Strategy Backtester")
ticker = st.sidebar.selectbox("Select a stock ticker", TOP_TICKERS)
end_date = datetime.now().date()
start_date = st.sidebar.date_input("Select start date", end_date - timedelta(days=4*365))

# Strategy selection
strategy = st.sidebar.selectbox("Select a strategy", ["MACD", "RSI", "ATR"])

# Strategy parameters
if strategy == "MACD":
    fast_period = st.sidebar.slider("Fast period", 5, 50, 12)
    slow_period = st.sidebar.slider("Slow period", 10, 100, 26)
    signal_period = st.sidebar.slider("Signal period", 5, 20, 9)
elif strategy == "RSI":
    rsi_period = st.sidebar.slider("RSI period", 5, 30, 14)
    overbought = st.sidebar.slider("Overbought level", 70, 90, 70)
    oversold = st.sidebar.slider("Oversold level", 10, 30, 30)
elif strategy == "ATR":
    atr_period = st.sidebar.slider("ATR period", 5, 30, 14)
    atr_multiplier = st.sidebar.slider("ATR multiplier", 1.0, 5.0, 2.0, 0.1)

# Download data
@st.cache_data
def download_data(ticker, start_date, end_date):
    data = yf.download(ticker, start=start_date, end=end_date)
    return data

data = download_data(ticker, start_date, end_date)

# Calculate indicators and signals
if strategy == "MACD":
    macd = ta.trend.MACD(data['Close'], fast_period, slow_period, signal_period)
    data['MACD'] = macd.macd()
    data['Signal'] = macd.macd_signal()
    data['Buy'] = (data['MACD'] > data['Signal']) & (data['MACD'].shift(1) <= data['Signal'].shift(1))
    data['Sell'] = (data['MACD'] < data['Signal']) & (data['MACD'].shift(1) >= data['Signal'].shift(1))
elif strategy == "RSI":
    data['RSI'] = ta.momentum.RSIIndicator(data['Close'], rsi_period).rsi()
    data['Buy'] = (data['RSI'] < oversold) & (data['RSI'].shift(1) >= oversold)
    data['Sell'] = (data['RSI'] > overbought) & (data['RSI'].shift(1) <= overbought)
elif strategy == "ATR":
    atr = ta.volatility.AverageTrueRange(data['High'], data['Low'], data['Close'], atr_period).average_true_range()
    data['Upper'] = data['Close'] + atr_multiplier * atr
    data['Lower'] = data['Close'] - atr_multiplier * atr
    data['Buy'] = (data['Close'] > data['Upper']) & (data['Close'].shift(1) <= data['Upper'].shift(1))
    data['Sell'] = (data['Close'] < data['Lower']) & (data['Close'].shift(1) >= data['Lower'].shift(1))

# Backtesting
initial_balance = 10000
balance = initial_balance
shares = 0
trades = []

for i in range(len(data)):
    if data['Buy'].iloc[i] and balance > 0:
        shares_to_buy = balance // data['Close'].iloc[i]
        cost = shares_to_buy * data['Close'].iloc[i]
        shares += shares_to_buy
        balance -= cost
        trades.append({
            'Date': data.index[i],
            'Action': 'Buy',
            'Price': data['Close'].iloc[i],
            'Shares': shares_to_buy,
            'Cost/Proceeds': cost,
            'Balance': balance,
            'Shares Held': shares,
            'Realized Gain/Loss': 0,
            'Cumulative Gain/Loss': (balance + shares * data['Close'].iloc[i]) - initial_balance
        })
    elif data['Sell'].iloc[i] and shares > 0:
        proceeds = shares * data['Close'].iloc[i]
        realized_gain = proceeds - (shares * trades[-1]['Price'])
        balance += proceeds
        shares = 0
        trades.append({
            'Date': data.index[i],
            'Action': 'Sell',
            'Price': data['Close'].iloc[i],
            'Shares': shares,
            'Cost/Proceeds': proceeds,
            'Balance': balance,
            'Shares Held': 0,
            'Realized Gain/Loss': realized_gain,
            'Cumulative Gain/Loss': balance - initial_balance
        })

# Calculate strategy performance
strategy_value = balance + shares * data['Close'].iloc[-1]
strategy_return = (strategy_value - initial_balance) / initial_balance * 100

# Calculate buy-and-hold performance
buy_and_hold_shares = initial_balance // data['Close'].iloc[0]
buy_and_hold_value = buy_and_hold_shares * data['Close'].iloc[-1]
buy_and_hold_return = (buy_and_hold_value - initial_balance) / initial_balance * 100

# Create interactive plot
fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.5, 0.3, 0.2])

# Stock price chart with buy/sell markers
fig.add_trace(go.Scatter(x=data.index, y=data['Close'], name='Stock Price'), row=1, col=1)
fig.add_trace(go.Scatter(x=data[data['Buy']].index, y=data[data['Buy']]['Close'], mode='markers', name='Buy Signal', marker=dict(symbol='triangle-up', size=10, color='green')), row=1, col=1)
fig.add_trace(go.Scatter(x=data[data['Sell']].index, y=data[data['Sell']]['Close'], mode='markers', name='Sell Signal', marker=dict(symbol='triangle-down', size=10, color='red')), row=1, col=1)

# Profit chart
trade_dates = [trade['Date'] for trade in trades]
cumulative_gains = [trade['Cumulative Gain/Loss'] for trade in trades]
fig.add_trace(go.Scatter(x=trade_dates, y=cumulative_gains, name='Strategy Profit'), row=2, col=1)
fig.add_trace(go.Scatter(x=data.index, y=(data['Close'] / data['Close'].iloc[0] - 1) * initial_balance, name='Buy and Hold'), row=2, col=1)

# Indicator chart
if strategy == "MACD":
    fig.add_trace(go.Scatter(x=data.index, y=data['MACD'], name='MACD'), row=3, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data['Signal'], name='Signal'), row=3, col=1)
elif strategy == "RSI":
    fig.add_trace(go.Scatter(x=data.index, y=data['RSI'], name='RSI'), row=3, col=1)
    fig.add_hline(y=overbought, line_dash="dash", line_color="red", row=3, col=1)
    fig.add_hline(y=oversold, line_dash="dash", line_color="green", row=3, col=1)
elif strategy == "ATR":
    fig.add_trace(go.Scatter(x=data.index, y=data['Upper'], name='Upper Band'), row=3, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data['Lower'], name='Lower Band'), row=3, col=1)

fig.update_layout(height=800, title_text=f"{ticker} - {strategy} Strategy Backtest")
st.plotly_chart(fig, use_container_width=True)

# Display performance metrics
st.subheader("Performance Metrics")
col1, col2 = st.columns(2)
col1.metric("Strategy Return", f"{strategy_return:.2f}%")
col2.metric("Buy and Hold Return", f"{buy_and_hold_return:.2f}%")

# Display trade details table
st.subheader("Trade Details")
trade_df = pd.DataFrame(trades)
st.dataframe(trade_df)
