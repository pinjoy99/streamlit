import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import ta

# Define the list of top 20 most traded stocks and ETFs
top_tickers = [
    "AAPL", "MSFT", "AMZN", "GOOGL", "META", "TSLA", "NVDA", "JPM", "JNJ", "V",
    "SPY", "QQQ", "IWM", "EFA", "VTI", "GLD", "VEA", "VWO", "BND", "AGG"
]

# Sidebar inputs
st.sidebar.header("Settings")
ticker = st.sidebar.selectbox("Select a stock or ETF", top_tickers)
years = st.sidebar.number_input("Number of years of historical data", min_value=1, max_value=10, value=5)
end_date = pd.Timestamp.now()
start_date = end_date - pd.DateOffset(years=years)

# Download data
@st.cache_data
def download_data(ticker, start_date, end_date):
    data = yf.download(ticker, start=start_date, end=end_date)
    return data

data = download_data(ticker, start_date, end_date)

# Technical indicator selection
indicator = st.sidebar.selectbox("Select a technical indicator", ["MACD", "RSI", "ATR"])

if indicator == "MACD":
    fast_period = st.sidebar.slider("MACD Fast Period", 5, 50, 12)
    slow_period = st.sidebar.slider("MACD Slow Period", 10, 100, 26)
    signal_period = st.sidebar.slider("MACD Signal Period", 5, 20, 9)
    
    data['macd'] = ta.trend.macd(data['Close'], window_fast=fast_period, window_slow=slow_period)
    data['macd_signal'] = ta.trend.macd_signal(data['Close'], window_fast=fast_period, window_slow=slow_period, window_sign=signal_period)
    data['macd_diff'] = ta.trend.macd_diff(data['Close'], window_fast=fast_period, window_slow=slow_period, window_sign=signal_period)
    
    buy_signal = (data['macd'] > data['macd_signal']) & (data['macd'].shift(1) <= data['macd_signal'].shift(1))
    sell_signal = (data['macd'] < data['macd_signal']) & (data['macd'].shift(1) >= data['macd_signal'].shift(1))

elif indicator == "RSI":
    rsi_period = st.sidebar.slider("RSI Period", 5, 30, 14)
    overbought = st.sidebar.slider("Overbought Level", 70, 90, 70)
    oversold = st.sidebar.slider("Oversold Level", 10, 30, 30)
    
    data['rsi'] = ta.momentum.rsi(data['Close'], window=rsi_period)
    
    buy_signal = (data['rsi'] < oversold) & (data['rsi'].shift(1) >= oversold)
    sell_signal = (data['rsi'] > overbought) & (data['rsi'].shift(1) <= overbought)

else:  # ATR
    atr_period = st.sidebar.slider("ATR Period", 5, 30, 14)
    atr_multiplier = st.sidebar.slider("ATR Multiplier", 1.0, 5.0, 2.0)
    
    data['atr'] = ta.volatility.average_true_range(data['High'], data['Low'], data['Close'], window=atr_period)
    data['upper_band'] = data['Close'] + atr_multiplier * data['atr']
    data['lower_band'] = data['Close'] - atr_multiplier * data['atr']
    
    buy_signal = (data['Close'] > data['upper_band']) & (data['Close'].shift(1) <= data['upper_band'].shift(1))
    sell_signal = (data['Close'] < data['lower_band']) & (data['Close'].shift(1) >= data['lower_band'].shift(1))

# Backtesting
data['Signal'] = 0
data.loc[buy_signal, 'Signal'] = 1
data.loc[sell_signal, 'Signal'] = -1

data['Position'] = data['Signal'].cumsum()
data['Position'] = data['Position'].clip(lower=0)  # Long-only strategy

data['Returns'] = data['Close'].pct_change()
data['Strategy_Returns'] = data['Position'].shift(1) * data['Returns']

# Calculate trade details
trades = data[data['Signal'] != 0].copy()
trades['Trade_Type'] = trades['Signal'].map({1: 'Buy', -1: 'Sell'})
trades['Price'] = data['Close']
trades['Profit/Loss'] = trades['Price'].diff()
trades['Profit/Loss'].iloc[0] = 0  # Set first trade P/L to 0

# Calculate cumulative returns
data['Cumulative_Returns'] = (1 + data['Strategy_Returns']).cumprod()
data['Benchmark_Returns'] = (1 + data['Returns']).cumprod()

# Create interactive plot
fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.5, 0.3, 0.2])

# Stock price chart
fig.add_trace(go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'], name='Price'), row=1, col=1)

# Buy and sell markers
fig.add_trace(go.Scatter(x=data[data['Signal'] == 1].index, y=data[data['Signal'] == 1]['Close'], mode='markers', marker=dict(symbol='triangle-up', size=10, color='green'), name='Buy Signal'), row=1, col=1)
fig.add_trace(go.Scatter(x=data[data['Signal'] == -1].index, y=data[data['Signal'] == -1]['Close'], mode='markers', marker=dict(symbol='triangle-down', size=10, color='red'), name='Sell Signal'), row=1, col=1)

# Profit/Loss chart
fig.add_trace(go.Scatter(x=data.index, y=data['Cumulative_Returns'], name='Strategy Returns'), row=2, col=1)
fig.add_trace(go.Scatter(x=data.index, y=data['Benchmark_Returns'], name='Benchmark Returns'), row=2, col=1)

# Indicator chart
if indicator == "MACD":
    fig.add_trace(go.Scatter(x=data.index, y=data['macd'], name='MACD'), row=3, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data['macd_signal'], name='Signal Line'), row=3, col=1)
    fig.add_bar(x=data.index, y=data['macd_diff'], name='MACD Histogram', row=3, col=1)
elif indicator == "RSI":
    fig.add_trace(go.Scatter(x=data.index, y=data['rsi'], name='RSI'), row=3, col=1)
    fig.add_hline(y=overbought, line_dash="dash", line_color="red", row=3, col=1)
    fig.add_hline(y=oversold, line_dash="dash", line_color="green", row=3, col=1)
else:  # ATR
    fig.add_trace(go.Scatter(x=data.index, y=data['atr'], name='ATR'), row=3, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data['upper_band'], name='Upper Band', line=dict(dash='dash')), row=1, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data['lower_band'], name='Lower Band', line=dict(dash='dash')), row=1, col=1)

fig.update_layout(height=800, title_text=f"{ticker} - {indicator} Strategy Backtest")
fig.update_xaxes(rangeslider_visible=False)

st.plotly_chart(fig, use_container_width=True)

# Display trade details
st.subheader("Trade Details")
st.dataframe(trades[['Trade_Type', 'Price', 'Profit/Loss']])

# Calculate and display overall performance
total_trades = len(trades)
profitable_trades = (trades['Profit/Loss'] > 0).sum()
loss_making_trades = (trades['Profit/Loss'] < 0).sum()
total_profit = trades['Profit/Loss'].sum()
max_drawdown = (data['Cumulative_Returns'] / data['Cumulative_Returns'].cummax() - 1).min()

st.subheader("Performance Summary")
col1, col2, col3 = st.columns(3)
col1.metric("Total Trades", total_trades)
col2.metric("Profitable Trades", profitable_trades)
col3.metric("Loss-making Trades", loss_making_trades)

col1, col2 = st.columns(2)
col1.metric("Total Profit/Loss", f"${total_profit:.2f}")
col2.metric("Max Drawdown", f"{max_drawdown:.2%}")

# Calculate and display unrealized profit/loss
current_position = data['Position'].iloc[-1]
last_price = data['Close'].iloc[-1]
cost_basis = trades[trades['Trade_Type'] == 'Buy']['Price'].iloc[-1] if current_position > 0 else 0
unrealized_pl = (last_price - cost_basis) * current_position if current_position > 0 else 0

st.subheader("Current Position")
col1, col2 = st.columns(2)
col1.metric("Current Position", current_position)
col2.metric("Unrealized Profit/Loss", f"${unrealized_pl:.2f}")
