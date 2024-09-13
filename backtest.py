import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from ta import add_all_ta_features
from datetime import datetime, timedelta

# Function to get top 20 most traded stocks and ETFs
def get_top_tickers():
    # This is a placeholder. In a real app, you'd fetch this data from a reliable source.
    return ['AAPL', 'MSFT', 'AMZN', 'GOOGL', 'FB', 'TSLA', 'NVDA', 'JPM', 'JNJ', 'V',
            'SPY', 'QQQ', 'IWM', 'EEM', 'GLD', 'VTI', 'VOO', 'IVV', 'EFA', 'XLF']

# Function to download stock data
def download_data(ticker, start_date, end_date):
    data = yf.download(ticker, start=start_date, end=end_date)
    return data

# Function to implement trading strategy
def implement_strategy(data, indicator, buy_threshold, sell_threshold):
    if indicator == 'MACD':
        data['MACD'] = data['Close'].ewm(span=12).mean() - data['Close'].ewm(span=26).mean()
        data['Signal'] = data['MACD'].ewm(span=9).mean()
        data['Buy'] = (data['MACD'] > data['Signal']) & (data['MACD'].shift(1) <= data['Signal'].shift(1))
        data['Sell'] = (data['MACD'] < data['Signal']) & (data['MACD'].shift(1) >= data['Signal'].shift(1))
    elif indicator == 'RSI':
        data['RSI'] = ta.momentum.rsi(data['Close'], window=14)
        data['Buy'] = (data['RSI'] < buy_threshold) & (data['RSI'].shift(1) >= buy_threshold)
        data['Sell'] = (data['RSI'] > sell_threshold) & (data['RSI'].shift(1) <= sell_threshold)
    elif indicator == 'ATR':
        data['ATR'] = ta.volatility.average_true_range(data['High'], data['Low'], data['Close'], window=14)
        data['Upper'] = data['Close'] + 2 * data['ATR']
        data['Lower'] = data['Close'] - 2 * data['ATR']
        data['Buy'] = data['Close'] < data['Lower']
        data['Sell'] = data['Close'] > data['Upper']
    
    return data

# Function to calculate strategy performance
def calculate_performance(data):
    data['Position'] = 0
    data.loc[data['Buy'], 'Position'] = 1
    data.loc[data['Sell'], 'Position'] = 0
    data['Position'] = data['Position'].fillna(method='ffill')
    
    data['Strategy'] = data['Position'].shift(1) * data['Close'].pct_change()
    data['Benchmark'] = data['Close'].pct_change()
    
    data['Strategy_Cum'] = (1 + data['Strategy']).cumprod()
    data['Benchmark_Cum'] = (1 + data['Benchmark']).cumprod()
    
    return data

# Function to create interactive plot
def create_plot(data, ticker):
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.05,
                        subplot_titles=(f'{ticker} Price', 'Cumulative Returns', 'Indicator'))
    
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'], name='Close Price'), row=1, col=1)
    fig.add_trace(go.Scatter(x=data[data['Buy']].index, y=data[data['Buy']]['Close'], 
                             mode='markers', name='Buy Signal', marker=dict(color='green', symbol='triangle-up', size=10)), row=1, col=1)
    fig.add_trace(go.Scatter(x=data[data['Sell']].index, y=data[data['Sell']]['Close'], 
                             mode='markers', name='Sell Signal', marker=dict(color='red', symbol='triangle-down', size=10)), row=1, col=1)
    
    fig.add_trace(go.Scatter(x=data.index, y=data['Strategy_Cum'], name='Strategy'), row=2, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data['Benchmark_Cum'], name='Benchmark'), row=2, col=1)
    
    if 'MACD' in data.columns:
        fig.add_trace(go.Scatter(x=data.index, y=data['MACD'], name='MACD'), row=3, col=1)
        fig.add_trace(go.Scatter(x=data.index, y=data['Signal'], name='Signal'), row=3, col=1)
    elif 'RSI' in data.columns:
        fig.add_trace(go.Scatter(x=data.index, y=data['RSI'], name='RSI'), row=3, col=1)
    elif 'ATR' in data.columns:
        fig.add_trace(go.Scatter(x=data.index, y=data['ATR'], name='ATR'), row=3, col=1)
    
    fig.update_layout(height=900, title_text=f"{ticker} Trading Strategy Backtest")
    return fig

# Function to calculate trade details
def calculate_trade_details(data):
    trades = pd.DataFrame(columns=['Entry Date', 'Exit Date', 'Entry Price', 'Exit Price', 'Profit/Loss', 'Cumulative P/L'])
    
    in_position = False
    entry_date = None
    entry_price = None
    cumulative_pl = 0
    
    for index, row in data.iterrows():
        if not in_position and row['Buy']:
            in_position = True
            entry_date = index
            entry_price = row['Close']
        elif in_position and row['Sell']:
            in_position = False
            exit_date = index
            exit_price = row['Close']
            profit_loss = (exit_price - entry_price) / entry_price
            cumulative_pl += profit_loss
            trades = trades.append({
                'Entry Date': entry_date,
                'Exit Date': exit_date,
                'Entry Price': entry_price,
                'Exit Price': exit_price,
                'Profit/Loss': f"{profit_loss:.2%}",
                'Cumulative P/L': f"{cumulative_pl:.2%}"
            }, ignore_index=True)
    
    return trades

# Streamlit app
st.title('Stock Trading Strategy Backtester')

# Sidebar
st.sidebar.header('Input Parameters')
ticker = st.sidebar.selectbox('Select Stock Ticker', get_top_tickers())
end_date = datetime.now()
start_date = st.sidebar.date_input('Start Date', end_date - timedelta(days=4*365))
end_date = st.sidebar.date_input('End Date', end_date)
indicator = st.sidebar.selectbox('Select Indicator', ['MACD', 'RSI', 'ATR'])
buy_threshold = st.sidebar.slider('Buy Threshold', 0, 100, 30)
sell_threshold = st.sidebar.slider('Sell Threshold', 0, 100, 70)

# Download data
data = download_data(ticker, start_date, end_date)

# Implement strategy
data = implement_strategy(data, indicator, buy_threshold, sell_threshold)

# Calculate performance
data = calculate_performance(data)

# Create plot
fig = create_plot(data, ticker)
st.plotly_chart(fig)

# Display trade details
st.subheader('Trade Details')
trade_details = calculate_trade_details(data)
st.table(trade_details)

# Display overall performance
st.subheader('Overall Performance')
total_return = data['Strategy_Cum'].iloc[-1] - 1
benchmark_return = data['Benchmark_Cum'].iloc[-1] - 1
st.write(f"Strategy Total Return: {total_return:.2%}")
st.write(f"Benchmark Total Return: {benchmark_return:.2%}")
