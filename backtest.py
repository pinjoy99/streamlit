import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import talib

# Define the list of top 20 most traded stocks and ETFs
top_tickers = ['SPY', 'QQQ', 'IWM', 'VXUS', 'RSP', 'EEM', 'BIL', 'XLF', 'SPLG', 'IVV', 'EFA', 'TLT', 'XLV', 'VTI', 'AAPL', 'MSFT', 'AMZN', 'GOOGL', 'NVDA', 'META']

# Sidebar inputs
st.sidebar.title("Stock Trading Backtest")
ticker = st.sidebar.selectbox("Select a stock ticker", top_tickers)
start_date = st.sidebar.date_input("Start date", value=pd.Timestamp.now() - pd.Timedelta(days=4*365))
end_date = st.sidebar.date_input("End date", value=pd.Timestamp.now())

# Technical indicator selection
indicator = st.sidebar.selectbox("Select a technical indicator", ["MACD", "RSI", "ATR"])

# Indicator parameters
if indicator == "MACD":
    fast_period = st.sidebar.slider("Fast period", 5, 30, 12)
    slow_period = st.sidebar.slider("Slow period", 10, 50, 26)
    signal_period = st.sidebar.slider("Signal period", 5, 20, 9)
elif indicator == "RSI":
    rsi_period = st.sidebar.slider("RSI period", 5, 30, 14)
    oversold = st.sidebar.slider("Oversold threshold", 10, 40, 30)
    overbought = st.sidebar.slider("Overbought threshold", 60, 90, 70)
elif indicator == "ATR":
    atr_period = st.sidebar.slider("ATR period", 5, 30, 14)
    atr_multiplier = st.sidebar.slider("ATR multiplier", 1.0, 5.0, 2.0, 0.1)

# Download historical data
@st.cache_data
def load_data(ticker, start_date, end_date):
    data = yf.download(ticker, start=start_date, end=end_date)
    return data

data = load_data(ticker, start_date, end_date)

# Calculate technical indicator
if indicator == "MACD":
    macd, signal, _ = talib.MACD(data['Close'], fastperiod=fast_period, slowperiod=slow_period, signalperiod=signal_period)
    data['MACD'] = macd
    data['Signal'] = signal
elif indicator == "RSI":
    data['RSI'] = talib.RSI(data['Close'], timeperiod=rsi_period)
elif indicator == "ATR":
    data['ATR'] = talib.ATR(data['High'], data['Low'], data['Close'], timeperiod=atr_period)

# Generate buy/sell signals
data['Position'] = 0
if indicator == "MACD":
    data.loc[data['MACD'] > data['Signal'], 'Position'] = 1
    data.loc[data['MACD'] <= data['Signal'], 'Position'] = 0
elif indicator == "RSI":
    data.loc[data['RSI'] < oversold, 'Position'] = 1
    data.loc[data['RSI'] > overbought, 'Position'] = 0
elif indicator == "ATR":
    data['UpperBand'] = data['Close'] + atr_multiplier * data['ATR']
    data['LowerBand'] = data['Close'] - atr_multiplier * data['ATR']
    data.loc[data['Close'] > data['UpperBand'].shift(1), 'Position'] = 1
    data.loc[data['Close'] < data['LowerBand'].shift(1), 'Position'] = 0

# Calculate returns
data['Returns'] = data['Close'].pct_change()
data['Strategy_Returns'] = data['Position'].shift(1) * data['Returns']
data['Cumulative_Returns'] = (1 + data['Strategy_Returns']).cumprod()
data['Buy_and_Hold_Returns'] = (1 + data['Returns']).cumprod()

# Create interactive plot
fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.5, 0.3, 0.2])

# Stock price chart with buy/sell markers
fig.add_trace(go.Scatter(x=data.index, y=data['Close'], name='Stock Price'), row=1, col=1)
fig.add_trace(go.Scatter(x=data[data['Position'] == 1].index, y=data[data['Position'] == 1]['Close'], 
                         mode='markers', name='Buy Signal', marker=dict(color='green', symbol='triangle-up', size=10)), row=1, col=1)
fig.add_trace(go.Scatter(x=data[data['Position'] == 0].index, y=data[data['Position'] == 0]['Close'], 
                         mode='markers', name='Sell Signal', marker=dict(color='red', symbol='triangle-down', size=10)), row=1, col=1)

# Cumulative returns chart
fig.add_trace(go.Scatter(x=data.index, y=data['Cumulative_Returns'], name='Strategy Returns'), row=2, col=1)
fig.add_trace(go.Scatter(x=data.index, y=data['Buy_and_Hold_Returns'], name='Buy and Hold Returns'), row=2, col=1)

# Indicator chart
if indicator == "MACD":
    fig.add_trace(go.Scatter(x=data.index, y=data['MACD'], name='MACD'), row=3, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data['Signal'], name='Signal'), row=3, col=1)
elif indicator == "RSI":
    fig.add_trace(go.Scatter(x=data.index, y=data['RSI'], name='RSI'), row=3, col=1)
    fig.add_hline(y=oversold, line_dash="dash", line_color="green", row=3, col=1)
    fig.add_hline(y=overbought, line_dash="dash", line_color="red", row=3, col=1)
elif indicator == "ATR":
    fig.add_trace(go.Scatter(x=data.index, y=data['ATR'], name='ATR'), row=3, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data['UpperBand'], name='Upper Band', line=dict(dash='dash')), row=1, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data['LowerBand'], name='Lower Band', line=dict(dash='dash')), row=1, col=1)

fig.update_layout(height=800, title_text=f"{ticker} Stock Trading Backtest")
st.plotly_chart(fig, use_container_width=True)

# Create trade details table
trades = data[data['Position'] != data['Position'].shift(1)].copy()
trades['Trade_Type'] = np.where(trades['Position'] == 1, 'Buy', 'Sell')
trades['Holding_Period'] = trades.index.to_series().diff().dt.days
trades['Realized_Gain_Loss'] = trades['Close'] - trades['Close'].shift(1)
trades['Cumulative_Gain_Loss'] = trades['Realized_Gain_Loss'].cumsum()

st.subheader("Trade Details")
st.dataframe(trades[['Trade_Type', 'Close', 'Holding_Period', 'Realized_Gain_Loss', 'Cumulative_Gain_Loss']])

# Performance metrics
total_return = data['Cumulative_Returns'].iloc[-1] - 1
buy_hold_return = data['Buy_and_Hold_Returns'].iloc[-1] - 1
sharpe_ratio = np.sqrt(252) * data['Strategy_Returns'].mean() / data['Strategy_Returns'].std()

st.subheader("Performance Metrics")
col1, col2, col3 = st.columns(3)
col1.metric("Total Return", f"{total_return:.2%}")
col2.metric("Buy & Hold Return", f"{buy_hold_return:.2%}")
col3.metric("Sharpe Ratio", f"{sharpe_ratio:.2f}")
