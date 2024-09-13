import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from ta import add_all_ta_features
from ta.trend import MACD
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange
from datetime import datetime, timedelta

# Function to get top 20 most traded stocks and ETFs
def get_top_tickers():
    # This would typically involve scraping or using an API
    # For simplicity, we'll use a hardcoded list
    return ['AAPL', 'MSFT', 'AMZN', 'GOOGL', 'FB', 'TSLA', 'NVDA', 'JPM', 'JNJ', 'V',
            'SPY', 'QQQ', 'IWM', 'EEM', 'VTI', 'GLD', 'XLF', 'VEA', 'VWO', 'BND']

# Function to download stock data
def get_stock_data(ticker, start_date, end_date):
    return yf.download(ticker, start=start_date, end=end_date)

# Function to implement trading strategy
def implement_strategy(data, indicator, params):
    if indicator == 'MACD':
        macd = MACD(data['Close'], **params)
        data['Signal'] = (macd.macd() > macd.macd_signal()).astype(int)
    elif indicator == 'RSI':
        rsi = RSIIndicator(data['Close'], **params)
        data['Signal'] = ((rsi.rsi() < 30).astype(int) - (rsi.rsi() > 70).astype(int))
    elif indicator == 'ATR':
        atr = AverageTrueRange(data['High'], data['Low'], data['Close'], **params)
        data['Signal'] = ((data['Close'] > data['Close'].shift(1) + atr.average_true_range()).astype(int) - 
                          (data['Close'] < data['Close'].shift(1) - atr.average_true_range()).astype(int))
    
    data['Position'] = data['Signal'].diff()
    
    return data

# Function to calculate returns
def calculate_returns(data):
    data['Strategy_Returns'] = data['Close'].pct_change() * data['Signal'].shift(1)
    data['Cumulative_Returns'] = (1 + data['Strategy_Returns']).cumprod()
    data['Buy_Hold_Returns'] = (1 + data['Close'].pct_change()).cumprod()
    return data

# Function to plot results
def plot_results(data, ticker):
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.05,
                        subplot_titles=(f'{ticker} Price', 'Profit/Loss', 'Indicator'))

    fig.add_trace(go.Scatter(x=data.index, y=data['Close'], name='Close Price'), row=1, col=1)
    fig.add_trace(go.Scatter(x=data[data['Position'] == 1].index, 
                             y=data[data['Position'] == 1]['Close'],
                             mode='markers', name='Buy', marker=dict(color='green', symbol='triangle-up', size=10)), row=1, col=1)
    fig.add_trace(go.Scatter(x=data[data['Position'] == -1].index, 
                             y=data[data['Position'] == -1]['Close'],
                             mode='markers', name='Sell', marker=dict(color='red', symbol='triangle-down', size=10)), row=1, col=1)

    fig.add_trace(go.Scatter(x=data.index, y=data['Cumulative_Returns'], name='Strategy Returns'), row=2, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data['Buy_Hold_Returns'], name='Buy & Hold Returns'), row=2, col=1)

    if 'MACD' in data.columns:
        fig.add_trace(go.Scatter(x=data.index, y=data['MACD'], name='MACD'), row=3, col=1)
        fig.add_trace(go.Scatter(x=data.index, y=data['MACD_Signal'], name='Signal Line'), row=3, col=1)
    elif 'RSI' in data.columns:
        fig.add_trace(go.Scatter(x=data.index, y=data['RSI'], name='RSI'), row=3, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
    elif 'ATR' in data.columns:
        fig.add_trace(go.Scatter(x=data.index, y=data['ATR'], name='ATR'), row=3, col=1)

    fig.update_layout(height=900, width=1000, title_text=f"{ticker} Trading Strategy Results")
    return fig

# Streamlit app
st.title('Stock Trading Strategy Backtester')

# Sidebar
st.sidebar.header('Input Parameters')

# Stock selection
tickers = get_top_tickers()
selected_ticker = st.sidebar.selectbox('Select a stock', tickers)

# Date range selection
end_date = datetime.now()
start_date = end_date - timedelta(days=4*365)
start_date = st.sidebar.date_input('Start date', start_date)
end_date = st.sidebar.date_input('End date', end_date)

# Strategy selection
strategy = st.sidebar.selectbox('Select a strategy', ['MACD', 'RSI', 'ATR'])

# Strategy parameters
if strategy == 'MACD':
    fast_period = st.sidebar.slider('Fast period', 5, 50, 12)
    slow_period = st.sidebar.slider('Slow period', 10, 100, 26)
    signal_period = st.sidebar.slider('Signal period', 5, 50, 9)
    params = {'window_fast': fast_period, 'window_slow': slow_period, 'window_sign': signal_period}
elif strategy == 'RSI':
    rsi_period = st.sidebar.slider('RSI period', 5, 50, 14)
    params = {'window': rsi_period}
elif strategy == 'ATR':
    atr_period = st.sidebar.slider('ATR period', 5, 50, 14)
    params = {'window': atr_period}

# Main app
if st.sidebar.button('Run Backtest'):
    # Get data
    data = get_stock_data(selected_ticker, start_date, end_date)
    
    # Implement strategy
    data = implement_strategy(data, strategy, params)
    
    # Calculate returns
    data = calculate_returns(data)
    
    # Plot results
    fig = plot_results(data, selected_ticker)
    st.plotly_chart(fig)
    
    # Display trade details
    trades = data[data['Position'] != 0].copy()
    trades['Holding_Period'] = trades.index.to_series().diff().dt.days
    trades['Realized_PnL'] = trades['Close'] * trades['Position'] * -1
    trades['Cumulative_PnL'] = trades['Realized_PnL'].cumsum()
    
    st.subheader('Trade Details')
    st.dataframe(trades[['Close', 'Position', 'Holding_Period', 'Realized_PnL', 'Cumulative_PnL']])

    # Display overall performance
    total_return = data['Cumulative_Returns'].iloc[-1] - 1
    buy_hold_return = data['Buy_Hold_Returns'].iloc[-1] - 1
    st.subheader('Overall Performance')
    st.write(f'Strategy Total Return: {total_return:.2%}')
    st.write(f'Buy & Hold Return: {buy_hold_return:.2%}')
