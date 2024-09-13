import streamlit as st
import pandas as pd
import yfinance as yf
import pandas_ta as ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

# Function to get top 20 most traded stocks and ETFs
def get_top_traded():
    # This is a placeholder. In a real app, you'd fetch this data dynamically.
    return ['SPY', 'QQQ', 'AAPL', 'TSLA', 'AMZN', 'NVDA', 'AMD', 'MSFT', 'GOOGL', 'META', 
            'BAC', 'F', 'INTC', 'XLF', 'PLTR', 'NIO', 'SOFI', 'AAL', 'CCL', 'SNAP']

# Function to download stock data
def download_data(ticker, start_date, end_date):
    return yf.download(ticker, start=start_date, end=end_date)

# Function to calculate indicators
def calculate_indicator(data, indicator, params):
    if indicator == 'MACD':
        return ta.macd(data['Close'], **params)
    elif indicator == 'RSI':
        return ta.rsi(data['Close'], **params)
    elif indicator == 'ATR':
        return ta.atr(data['High'], data['Low'], data['Close'], **params)

# Function to generate buy/sell signals
def generate_signals(data, indicator_data, indicator):
    signals = pd.DataFrame(index=data.index)
    signals['Signal'] = 0
    
    if indicator == 'MACD':
        signals.loc[indicator_data['MACD_12_26_9'] > indicator_data['MACDs_12_26_9'], 'Signal'] = 1
        signals.loc[indicator_data['MACD_12_26_9'] < indicator_data['MACDs_12_26_9'], 'Signal'] = -1
    elif indicator == 'RSI':
        signals.loc[indicator_data > 70, 'Signal'] = -1
        signals.loc[indicator_data < 30, 'Signal'] = 1
    elif indicator == 'ATR':
        signals['Signal'] = 0  # ATR doesn't generate buy/sell signals directly
    
    return signals

# Function to backtest strategy
def backtest_strategy(data, signals):
    position = 0
    trades = []
    for i in range(len(data)):
        if signals['Signal'].iloc[i] == 1 and position == 0:
            position = 1
            entry_price = data['Close'].iloc[i]
            entry_date = data.index[i]
        elif (signals['Signal'].iloc[i] == -1 or i == len(data) - 1) and position == 1:
            position = 0
            exit_price = data['Close'].iloc[i]
            exit_date = data.index[i]
            trades.append({
                'Entry Date': entry_date,
                'Entry Price': entry_price,
                'Exit Date': exit_date,
                'Exit Price': exit_price,
                'Profit': exit_price - entry_price
            })
    
    return pd.DataFrame(trades)

# Streamlit app
st.title('Stock Trading Strategy Backtester')

# Sidebar
st.sidebar.header('Input Parameters')
ticker = st.sidebar.selectbox('Select Stock', get_top_traded())
end_date = datetime.now().date()
start_date = st.sidebar.date_input('Start Date', end_date - timedelta(days=4*365))
indicator = st.sidebar.selectbox('Select Indicator', ['MACD', 'RSI', 'ATR'])

if indicator == 'MACD':
    fast = st.sidebar.slider('MACD Fast Period', 5, 30, 12)
    slow = st.sidebar.slider('MACD Slow Period', 10, 50, 26)
    signal = st.sidebar.slider('MACD Signal Period', 5, 20, 9)
    params = {'fast': fast, 'slow': slow, 'signal': signal}
elif indicator == 'RSI':
    length = st.sidebar.slider('RSI Length', 5, 30, 14)
    params = {'length': length}
elif indicator == 'ATR':
    length = st.sidebar.slider('ATR Length', 5, 30, 14)
    params = {'length': length}

# Download data
data = download_data(ticker, start_date, end_date)

# Calculate indicator
indicator_data = calculate_indicator(data, indicator, params)

# Generate signals
signals = generate_signals(data, indicator_data, indicator)

# Backtest strategy
trades = backtest_strategy(data, signals)

# Calculate cumulative returns
data['Strategy'] = (data['Close'].pct_change() * signals['Signal'].shift(1)).cumsum()
data['Buy and Hold'] = data['Close'].pct_change().cumsum()

# Create interactive plot
fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.05, 
                    subplot_titles=('Stock Price', 'Cumulative Returns', indicator))

# Stock price subplot
fig.add_trace(go.Scatter(x=data.index, y=data['Close'], name='Close Price'), row=1, col=1)
for trade in trades.itertuples():
    fig.add_trace(go.Scatter(x=[trade.Entry_Date], y=[trade.Entry_Price], mode='markers', 
                             marker=dict(symbol='triangle-up', size=10, color='green'), 
                             name='Buy'), row=1, col=1)
    fig.add_trace(go.Scatter(x=[trade.Exit_Date], y=[trade.Exit_Price], mode='markers', 
                             marker=dict(symbol='triangle-down', size=10, color='red'), 
                             name='Sell'), row=1, col=1)

# Cumulative returns subplot
fig.add_trace(go.Scatter(x=data.index, y=data['Strategy'], name='Strategy'), row=2, col=1)
fig.add_trace(go.Scatter(x=data.index, y=data['Buy and Hold'], name='Buy and Hold'), row=2, col=1)

# Indicator subplot
if indicator == 'MACD':
    fig.add_trace(go.Scatter(x=data.index, y=indicator_data['MACD_12_26_9'], name='MACD'), row=3, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=indicator_data['MACDs_12_26_9'], name='Signal'), row=3, col=1)
elif indicator == 'RSI':
    fig.add_trace(go.Scatter(x=data.index, y=indicator_data, name='RSI'), row=3, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
elif indicator == 'ATR':
    fig.add_trace(go.Scatter(x=data.index, y=indicator_data, name='ATR'), row=3, col=1)

fig.update_layout(height=900, title_text=f"{ticker} Trading Strategy Backtest")
st.plotly_chart(fig, use_container_width=True)

# Display trade details
st.subheader('Trade Details')
st.dataframe(trades)

# Display strategy performance
total_profit = trades['Profit'].sum()
num_trades = len(trades)
win_rate = (trades['Profit'] > 0).mean()

st.subheader('Strategy Performance')
col1, col2, col3 = st.columns(3)
col1.metric("Total Profit", f"${total_profit:.2f}")
col2.metric("Number of Trades", num_trades)
col3.metric("Win Rate", f"{win_rate:.2%}")
