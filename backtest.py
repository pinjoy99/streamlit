import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import ta

# Define the list of top 30 most traded stocks and ETFs
top_tickers = ['SPY', 'QQQ', 'IWM', 'AAPL', 'TSLA', 'NVDA', 'AMD', 'AMZN', 'MSFT', 'META', 'GOOGL', 'BAC', 'F', 'NIO', 'PLTR', 'INTC', 'AAL', 'CCL', 'SNAP', 'PFE', 'XLF', 'EEM', 'VWO', 'EFA', 'HYG', 'GDX', 'XLE', 'SLV', 'USO', 'FXI']

# Sidebar inputs
st.sidebar.header('Backtest Parameters')
ticker = st.sidebar.selectbox('Select Stock/ETF', top_tickers)
start_date = st.sidebar.date_input('Start Date', value=pd.to_datetime('today') - pd.DateOffset(years=4))
end_date = st.sidebar.date_input('End Date', value=pd.to_datetime('today'))

indicator = st.sidebar.selectbox('Select Indicator', ['MACD', 'RSI', 'ATR'])

if indicator == 'MACD':
    fast_period = st.sidebar.slider('Fast Period', 5, 50, 12)
    slow_period = st.sidebar.slider('Slow Period', 10, 100, 26)
    signal_period = st.sidebar.slider('Signal Period', 5, 20, 9)
elif indicator == 'RSI':
    rsi_period = st.sidebar.slider('RSI Period', 5, 30, 14)
    overbought = st.sidebar.slider('Overbought Level', 50, 90, 70)
    oversold = st.sidebar.slider('Oversold Level', 10, 50, 30)
elif indicator == 'ATR':
    atr_period = st.sidebar.slider('ATR Period', 5, 30, 14)
    atr_multiplier = st.sidebar.slider('ATR Multiplier', 1.0, 5.0, 2.0, 0.1)

# Download data
@st.cache_data
def download_data(ticker, start_date, end_date):
    data = yf.download(ticker, start=start_date, end=end_date)
    return data

data = download_data(ticker, start_date, end_date)

# Calculate indicators
if indicator == 'MACD':
    macd = ta.trend.MACD(data['Close'], fast_period, slow_period, signal_period)
    data['MACD'] = macd.macd()
    data['Signal'] = macd.macd_signal()
    data['MACD_Hist'] = macd.macd_diff()
    data['Buy_Signal'] = (data['MACD'] > data['Signal']) & (data['MACD'].shift(1) <= data['Signal'].shift(1))
    data['Sell_Signal'] = (data['MACD'] < data['Signal']) & (data['MACD'].shift(1) >= data['Signal'].shift(1))
elif indicator == 'RSI':
    data['RSI'] = ta.momentum.RSIIndicator(data['Close'], rsi_period).rsi()
    data['Buy_Signal'] = (data['RSI'] < oversold) & (data['RSI'].shift(1) >= oversold)
    data['Sell_Signal'] = (data['RSI'] > overbought) & (data['RSI'].shift(1) <= overbought)
elif indicator == 'ATR':
    atr = ta.volatility.AverageTrueRange(data['High'], data['Low'], data['Close'], atr_period).average_true_range()
    data['ATR'] = atr
    data['Upper_Band'] = data['Close'] + atr_multiplier * atr
    data['Lower_Band'] = data['Close'] - atr_multiplier * atr
    data['Buy_Signal'] = (data['Close'] > data['Upper_Band']) & (data['Close'].shift(1) <= data['Upper_Band'].shift(1))
    data['Sell_Signal'] = (data['Close'] < data['Lower_Band']) & (data['Close'].shift(1) >= data['Lower_Band'].shift(1))

# Backtest strategy
def backtest_strategy(data):
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
            trades.append({
                'Entry Date': entry_date,
                'Entry Price': entry_price,
                'Exit Date': exit_date,
                'Exit Price': exit_price,
                'Profit/Loss': (exit_price - entry_price) / entry_price
            })
    
    return pd.DataFrame(trades)

trades = backtest_strategy(data)

# Calculate cumulative returns
data['Strategy_Return'] = 0
data.loc[data['Buy_Signal'], 'Strategy_Return'] = data['Close'].pct_change()
data['Strategy_Cumulative_Return'] = (1 + data['Strategy_Return']).cumprod()
data['Buy_and_Hold_Return'] = data['Close'].pct_change()
data['Buy_and_Hold_Cumulative_Return'] = (1 + data['Buy_and_Hold_Return']).cumprod()

# Create interactive plot
fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.5, 0.3, 0.2])

# Price chart with buy/sell markers
fig.add_trace(go.Scatter(x=data.index, y=data['Close'], name='Close Price'), row=1, col=1)
fig.add_trace(go.Scatter(x=data[data['Buy_Signal']].index, y=data[data['Buy_Signal']]['Close'], mode='markers', name='Buy Signal', marker=dict(symbol='triangle-up', size=10, color='green')), row=1, col=1)
fig.add_trace(go.Scatter(x=data[data['Sell_Signal']].index, y=data[data['Sell_Signal']]['Close'], mode='markers', name='Sell Signal', marker=dict(symbol='triangle-down', size=10, color='red')), row=1, col=1)

# Cumulative return chart
fig.add_trace(go.Scatter(x=data.index, y=data['Strategy_Cumulative_Return'], name='Strategy Return'), row=2, col=1)
fig.add_trace(go.Scatter(x=data.index, y=data['Buy_and_Hold_Cumulative_Return'], name='Buy and Hold Return'), row=2, col=1)

# Indicator chart
if indicator == 'MACD':
    fig.add_trace(go.Scatter(x=data.index, y=data['MACD'], name='MACD'), row=3, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data['Signal'], name='Signal'), row=3, col=1)
    fig.add_bar(x=data.index, y=data['MACD_Hist'], name='MACD Histogram', row=3, col=1)
elif indicator == 'RSI':
    fig.add_trace(go.Scatter(x=data.index, y=data['RSI'], name='RSI'), row=3, col=1)
    fig.add_hline(y=overbought, line_dash="dash", line_color="red", row=3, col=1)
    fig.add_hline(y=oversold, line_dash="dash", line_color="green", row=3, col=1)
elif indicator == 'ATR':
    fig.add_trace(go.Scatter(x=data.index, y=data['ATR'], name='ATR'), row=3, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data['Upper_Band'], name='Upper Band', line=dict(dash='dash')), row=1, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data['Lower_Band'], name='Lower Band', line=dict(dash='dash')), row=1, col=1)

fig.update_layout(height=800, title_text=f"{ticker} Backtest Results")
st.plotly_chart(fig, use_container_width=True)

# Display trade details
st.subheader('Trade Details')
trades['Cumulative P/L'] = trades['Profit/Loss'].cumsum()
st.dataframe(trades)

# Display overall performance
total_return = trades['Profit/Loss'].sum()
num_trades = len(trades)
win_rate = (trades['Profit/Loss'] > 0).mean()

st.subheader('Overall Performance')
col1, col2, col3 = st.columns(3)
col1.metric('Total Return', f'{total_return:.2%}')
col2.metric('Number of Trades', num_trades)
col3.metric('Win Rate', f'{win_rate:.2%}')
