import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from ta.trend import MACD
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange

# Define the list of top 20 most traded stocks and ETFs
top_tickers = ['AAPL', 'MSFT', 'AMZN', 'GOOGL', 'FB', 'TSLA', 'BRK-B', 'JPM', 'JNJ', 'V', 
               'PG', 'UNH', 'HD', 'BAC', 'DIS', 'ADBE', 'NFLX', 'CRM', 'CMCSA', 'XOM']

# Sidebar inputs
st.sidebar.header('Input Parameters')
ticker = st.sidebar.selectbox('Select Stock Ticker', top_tickers)
start_date = st.sidebar.date_input('Start Date', value=pd.to_datetime('today') - pd.DateOffset(years=4))
end_date = st.sidebar.date_input('End Date', value=pd.to_datetime('today'))

indicator = st.sidebar.selectbox('Select Indicator', ['MACD', 'RSI', 'ATR'])

if indicator == 'MACD':
    fast_period = st.sidebar.slider('Fast Period', 5, 50, 12)
    slow_period = st.sidebar.slider('Slow Period', 10, 100, 26)
    signal_period = st.sidebar.slider('Signal Period', 5, 50, 9)
elif indicator == 'RSI':
    rsi_period = st.sidebar.slider('RSI Period', 5, 50, 14)
    rsi_overbought = st.sidebar.slider('Overbought Level', 50, 90, 70)
    rsi_oversold = st.sidebar.slider('Oversold Level', 10, 50, 30)
elif indicator == 'ATR':
    atr_period = st.sidebar.slider('ATR Period', 5, 50, 14)
    atr_multiplier = st.sidebar.slider('ATR Multiplier', 1.0, 5.0, 2.0, 0.1)

# Download data
@st.cache_data
def download_data(ticker, start_date, end_date):
    data = yf.download(ticker, start=start_date, end=end_date)
    return data

data = download_data(ticker, start_date, end_date)

# Calculate indicators
if indicator == 'MACD':
    macd = MACD(data['Close'], window_fast=fast_period, window_slow=slow_period, window_sign=signal_period)
    data['MACD'] = macd.macd()
    data['Signal'] = macd.macd_signal()
    data['MACD_Hist'] = macd.macd_diff()
    data['Buy_Signal'] = (data['MACD'] > data['Signal']) & (data['MACD'].shift(1) <= data['Signal'].shift(1))
    data['Sell_Signal'] = (data['MACD'] < data['Signal']) & (data['MACD'].shift(1) >= data['Signal'].shift(1))
elif indicator == 'RSI':
    rsi = RSIIndicator(data['Close'], window=rsi_period)
    data['RSI'] = rsi.rsi()
    data['Buy_Signal'] = (data['RSI'] < rsi_oversold) & (data['RSI'].shift(1) >= rsi_oversold)
    data['Sell_Signal'] = (data['RSI'] > rsi_overbought) & (data['RSI'].shift(1) <= rsi_overbought)
elif indicator == 'ATR':
    atr = AverageTrueRange(data['High'], data['Low'], data['Close'], window=atr_period)
    data['ATR'] = atr.average_true_range()
    data['Upper_Band'] = data['Close'] + atr_multiplier * data['ATR']
    data['Lower_Band'] = data['Close'] - atr_multiplier * data['ATR']
    data['Buy_Signal'] = (data['Close'] > data['Upper_Band']) & (data['Close'].shift(1) <= data['Upper_Band'].shift(1))
    data['Sell_Signal'] = (data['Close'] < data['Lower_Band']) & (data['Close'].shift(1) >= data['Lower_Band'].shift(1))

# Backtesting
data['Position'] = np.nan
data.loc[data['Buy_Signal'], 'Position'] = 1
data.loc[data['Sell_Signal'], 'Position'] = 0
data['Position'] = data['Position'].ffill().fillna(0)
data['Strategy_Return'] = data['Position'].shift(1) * data['Close'].pct_change()
data['Cumulative_Strategy_Return'] = (1 + data['Strategy_Return']).cumprod()
data['Cumulative_Market_Return'] = (1 + data['Close'].pct_change()).cumprod()

# Create interactive plot
fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.05, 
                    subplot_titles=('Stock Price', 'Cumulative Returns', indicator))

# Stock price subplot
fig.add_trace(go.Scatter(x=data.index, y=data['Close'], name='Close Price'), row=1, col=1)
fig.add_trace(go.Scatter(x=data[data['Buy_Signal']].index, y=data[data['Buy_Signal']]['Close'], 
                         mode='markers', name='Buy Signal', marker=dict(color='green', symbol='triangle-up', size=10)), row=1, col=1)
fig.add_trace(go.Scatter(x=data[data['Sell_Signal']].index, y=data[data['Sell_Signal']]['Close'], 
                         mode='markers', name='Sell Signal', marker=dict(color='red', symbol='triangle-down', size=10)), row=1, col=1)

# Cumulative returns subplot
fig.add_trace(go.Scatter(x=data.index, y=data['Cumulative_Strategy_Return'], name='Strategy'), row=2, col=1)
fig.add_trace(go.Scatter(x=data.index, y=data['Cumulative_Market_Return'], name='Buy and Hold'), row=2, col=1)

# Indicator subplot
if indicator == 'MACD':
    fig.add_trace(go.Scatter(x=data.index, y=data['MACD'], name='MACD'), row=3, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data['Signal'], name='Signal'), row=3, col=1)
    fig.add_bar(x=data.index, y=data['MACD_Hist'], name='MACD Histogram', row=3, col=1)
elif indicator == 'RSI':
    fig.add_trace(go.Scatter(x=data.index, y=data['RSI'], name='RSI'), row=3, col=1)
    fig.add_hline(y=rsi_overbought, line_dash="dash", line_color="red", row=3, col=1)
    fig.add_hline(y=rsi_oversold, line_dash="dash", line_color="green", row=3, col=1)
elif indicator == 'ATR':
    fig.add_trace(go.Scatter(x=data.index, y=data['ATR'], name='ATR'), row=3, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data['Upper_Band'], name='Upper Band', line=dict(dash='dash')), row=1, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data['Lower_Band'], name='Lower Band', line=dict(dash='dash')), row=1, col=1)

fig.update_layout(height=900, title_text=f"Backtesting Results for {ticker}")
st.plotly_chart(fig, use_container_width=True)

# Create trade details table
trades = data[data['Position'] != data['Position'].shift(1)].copy()
trades['Trade_Type'] = np.where(trades['Position'] == 1, 'Buy', 'Sell')
trades['Price'] = data['Close']
trades['Holding_Period'] = (trades.index - pd.Series(trades.index).shift(1)).days
trades['Profit_Loss'] = trades['Close'] - trades['Close'].shift(1)
trades['Cumulative_Profit_Loss'] = trades['Profit_Loss'].cumsum()

st.subheader('Trade Details')
st.dataframe(trades[['Trade_Type', 'Price', 'Holding_Period', 'Profit_Loss', 'Cumulative_Profit_Loss']])

# Display performance metrics
total_return = data['Cumulative_Strategy_Return'].iloc[-1] - 1
market_return = data['Cumulative_Market_Return'].iloc[-1] - 1
sharpe_ratio = np.sqrt(252) * data['Strategy_Return'].mean() / data['Strategy_Return'].std()

st.subheader('Performance Metrics')
col1, col2, col3 = st.columns(3)
col1.metric("Total Return", f"{total_return:.2%}")
col2.metric("Market Return", f"{market_return:.2%}")
col3.metric("Sharpe Ratio", f"{sharpe_ratio:.2f}")
