import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import ta

# List of top 20 most traded stocks and ETFs
top_tickers = ['AAPL', 'MSFT', 'AMZN', 'GOOGL', 'FB', 'TSLA', 'NVDA', 'JPM', 'JNJ', 'V', 'PG', 'UNH', 'HD', 'BAC', 'MA', 'DIS', 'ADBE', 'CRM', 'NFLX', 'CMCSA']

# Sidebar inputs
st.sidebar.title("Stock Trading Strategy Backtester")
ticker = st.sidebar.selectbox("Select a stock ticker", top_tickers)
years = st.sidebar.number_input("Number of years of historical data", min_value=1, max_value=10, value=5)
indicator = st.sidebar.selectbox("Select an indicator", ["MACD", "RSI", "ATR"])

# Indicator parameters
if indicator == "MACD":
    fast_period = st.sidebar.number_input("Fast period", min_value=1, max_value=50, value=12)
    slow_period = st.sidebar.number_input("Slow period", min_value=1, max_value=100, value=26)
    signal_period = st.sidebar.number_input("Signal period", min_value=1, max_value=50, value=9)
elif indicator == "RSI":
    rsi_period = st.sidebar.number_input("RSI period", min_value=1, max_value=50, value=14)
    overbought = st.sidebar.number_input("Overbought level", min_value=50, max_value=100, value=70)
    oversold = st.sidebar.number_input("Oversold level", min_value=0, max_value=50, value=30)
elif indicator == "ATR":
    atr_period = st.sidebar.number_input("ATR period", min_value=1, max_value=50, value=14)
    atr_multiplier = st.sidebar.number_input("ATR multiplier", min_value=0.1, max_value=5.0, value=2.0, step=0.1)

# Download historical data
end_date = pd.Timestamp.now()
start_date = end_date - pd.DateOffset(years=years)
data = yf.download(ticker, start=start_date, end=end_date)

# Calculate indicators
if indicator == "MACD":
    data['MACD'] = ta.trend.macd(data['Close'], fast_period, slow_period, signal_period)
    data['Signal'] = ta.trend.macd_signal(data['Close'], fast_period, slow_period, signal_period)
elif indicator == "RSI":
    data['RSI'] = ta.momentum.rsi(data['Close'], window=rsi_period)
elif indicator == "ATR":
    data['ATR'] = ta.volatility.average_true_range(data['High'], data['Low'], data['Close'], window=atr_period)
    data['Upper_Band'] = data['Close'] + atr_multiplier * data['ATR']
    data['Lower_Band'] = data['Close'] - atr_multiplier * data['ATR']

# Generate trading signals
data['Signal'] = 0
if indicator == "MACD":
    data.loc[data['MACD'] > data['Signal'], 'Signal'] = 1
    data.loc[data['MACD'] < data['Signal'], 'Signal'] = -1
elif indicator == "RSI":
    data.loc[data['RSI'] < oversold, 'Signal'] = 1
    data.loc[data['RSI'] > overbought, 'Signal'] = -1
elif indicator == "ATR":
    data.loc[data['Close'] > data['Upper_Band'].shift(1), 'Signal'] = 1
    data.loc[data['Close'] < data['Lower_Band'].shift(1), 'Signal'] = -1

# Calculate returns
data['Returns'] = data['Close'].pct_change()
data['Strategy_Returns'] = data['Signal'].shift(1) * data['Returns']
data['Cumulative_Returns'] = (1 + data['Strategy_Returns']).cumprod()
data['Buy_and_Hold_Returns'] = (1 + data['Returns']).cumprod()

# Create interactive plot
fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.05, 
                    subplot_titles=('Stock Price', 'Profit/Loss', 'Indicator'))

# Stock price chart
fig.add_trace(go.Scatter(x=data.index, y=data['Close'], name='Close Price'), row=1, col=1)

# Profit/Loss chart
fig.add_trace(go.Scatter(x=data.index, y=data['Cumulative_Returns'], name='Strategy Returns'), row=2, col=1)
fig.add_trace(go.Scatter(x=data.index, y=data['Buy_and_Hold_Returns'], name='Buy and Hold Returns'), row=2, col=1)

# Indicator chart
if indicator == "MACD":
    fig.add_trace(go.Scatter(x=data.index, y=data['MACD'], name='MACD'), row=3, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data['Signal'], name='Signal Line'), row=3, col=1)
elif indicator == "RSI":
    fig.add_trace(go.Scatter(x=data.index, y=data['RSI'], name='RSI'), row=3, col=1)
    fig.add_hline(y=overbought, line_dash="dash", line_color="red", row=3, col=1)
    fig.add_hline(y=oversold, line_dash="dash", line_color="green", row=3, col=1)
elif indicator == "ATR":
    fig.add_trace(go.Scatter(x=data.index, y=data['ATR'], name='ATR'), row=3, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data['Upper_Band'], name='Upper Band'), row=3, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data['Lower_Band'], name='Lower Band'), row=3, col=1)

# Add buy/sell marks
buy_signals = data[data['Signal'] == 1]
sell_signals = data[data['Signal'] == -1]
fig.add_trace(go.Scatter(x=buy_signals.index, y=buy_signals['Close'], mode='markers', 
                         marker=dict(symbol='triangle-up', size=10, color='green'), name='Buy'), row=1, col=1)
fig.add_trace(go.Scatter(x=sell_signals.index, y=sell_signals['Close'], mode='markers', 
                         marker=dict(symbol='triangle-down', size=10, color='red'), name='Sell'), row=1, col=1)

fig.update_layout(height=900, title_text=f"{ticker} - {indicator} Strategy Backtest")
st.plotly_chart(fig, use_container_width=True)

# Create trade details table
trades = data[data['Signal'] != 0].copy()
trades['Trade_Type'] = trades['Signal'].map({1: 'Buy', -1: 'Sell'})
trades['Holding_Period'] = trades.index.to_series().diff().dt.days
trades['Realized_Gain_Loss'] = trades['Strategy_Returns'].cumsum()
trades['Cumulative_Gain_Loss'] = trades['Realized_Gain_Loss'].cumsum()

st.subheader("Trade Details")
st.dataframe(trades[['Trade_Type', 'Close', 'Holding_Period', 'Realized_Gain_Loss', 'Cumulative_Gain_Loss']])

# Display performance metrics
total_return = data['Cumulative_Returns'].iloc[-1] - 1
buy_hold_return = data['Buy_and_Hold_Returns'].iloc[-1] - 1
sharpe_ratio = data['Strategy_Returns'].mean() / data['Strategy_Returns'].std() * (252 ** 0.5)

st.subheader("Performance Metrics")
col1, col2, col3 = st.columns(3)
col1.metric("Total Return", f"{total_return:.2%}")
col2.metric("Buy & Hold Return", f"{buy_hold_return:.2%}")
col3.metric("Sharpe Ratio", f"{sharpe_ratio:.2f}")
