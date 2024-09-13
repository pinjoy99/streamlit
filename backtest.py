import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from ta.trend import MACD
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange

# Function to download stock data
def get_stock_data(ticker, start_date, end_date):
    return yf.download(ticker, start=start_date, end=end_date)

# Function to calculate indicators
def calculate_indicator(data, indicator, **kwargs):
    if indicator == 'MACD':
        macd = MACD(data['Close'], **kwargs)
        return macd.macd(), macd.macd_signal()
    elif indicator == 'RSI':
        rsi = RSIIndicator(data['Close'], **kwargs)
        return rsi.rsi()
    elif indicator == 'ATR':
        atr = AverageTrueRange(data['High'], data['Low'], data['Close'], **kwargs)
        return atr.average_true_range()

# Function to implement trading strategy
def implement_strategy(data, indicator_values, indicator_type):
    buy_signals = []
    sell_signals = []
    position = 0
    
    if indicator_type == 'MACD':
        macd, signal = indicator_values
        for i in range(len(data)):
            if macd[i] > signal[i] and position == 0:
                buy_signals.append(data['Close'].iloc[i])
                sell_signals.append(np.nan)
                position = 1
            elif macd[i] < signal[i] and position == 1:
                sell_signals.append(data['Close'].iloc[i])
                buy_signals.append(np.nan)
                position = 0
            else:
                buy_signals.append(np.nan)
                sell_signals.append(np.nan)
    elif indicator_type == 'RSI':
        for i in range(len(data)):
            if indicator_values[i] < 30 and position == 0:
                buy_signals.append(data['Close'].iloc[i])
                sell_signals.append(np.nan)
                position = 1
            elif indicator_values[i] > 70 and position == 1:
                sell_signals.append(data['Close'].iloc[i])
                buy_signals.append(np.nan)
                position = 0
            else:
                buy_signals.append(np.nan)
                sell_signals.append(np.nan)
    elif indicator_type == 'ATR':
        for i in range(len(data)):
            if indicator_values[i] > data['Close'].iloc[i] * 0.02 and position == 0:  # Buy if ATR > 2% of price
                buy_signals.append(data['Close'].iloc[i])
                sell_signals.append(np.nan)
                position = 1
            elif indicator_values[i] < data['Close'].iloc[i] * 0.01 and position == 1:  # Sell if ATR < 1% of price
                sell_signals.append(data['Close'].iloc[i])
                buy_signals.append(np.nan)
                position = 0
            else:
                buy_signals.append(np.nan)
                sell_signals.append(np.nan)
    
    return buy_signals, sell_signals

# Function to calculate profit/loss
def calculate_pnl(data, buy_signals, sell_signals):
    pnl = [0]
    position = 0
    entry_price = 0
    for i in range(1, len(data)):
        if not np.isnan(buy_signals[i]) and position == 0:
            entry_price = buy_signals[i]
            position = 1
        elif not np.isnan(sell_signals[i]) and position == 1:
            pnl.append(pnl[-1] + (sell_signals[i] - entry_price))
            position = 0
        else:
            pnl.append(pnl[-1])
    return pnl

# Streamlit app
st.title('Stock Trading Strategy Backtester')

# User inputs
ticker = st.text_input('Enter stock ticker (e.g., AAPL)', 'AAPL')
start_date = st.date_input('Start date')
end_date = st.date_input('End date')
indicator = st.selectbox('Select indicator', ['MACD', 'RSI', 'ATR'])

if st.button('Run Backtest'):
    # Download data
    data = get_stock_data(ticker, start_date, end_date)
    
    # Calculate indicator
    if indicator == 'MACD':
        indicator_values = calculate_indicator(data, indicator)
    else:
        indicator_values = calculate_indicator(data, indicator)
    
    # Implement strategy
    buy_signals, sell_signals = implement_strategy(data, indicator_values, indicator)
    
    # Calculate profit/loss
    pnl = calculate_pnl(data, buy_signals, sell_signals)
    
    # Create subplots
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.05,
                        subplot_titles=('Stock Price', 'Profit/Loss', f'{indicator} Indicator'))
    
    # Stock price chart with buy/sell markers
    fig.add_trace(go.Candlestick(x=data.index, open=data['Open'], high=data['High'],
                                 low=data['Low'], close=data['Close'], name='Price'),
                  row=1, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=buy_signals, mode='markers',
                             marker=dict(symbol='triangle-up', size=10, color='green'),
                             name='Buy Signal'),
                  row=1, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=sell_signals, mode='markers',
                             marker=dict(symbol='triangle-down', size=10, color='red'),
                             name='Sell Signal'),
                  row=1, col=1)
    
    # Profit/Loss chart
    fig.add_trace(go.Scatter(x=data.index, y=pnl, name='Profit/Loss'),
                  row=2, col=1)
    
    # Indicator chart
    if indicator == 'MACD':
        fig.add_trace(go.Scatter(x=data.index, y=indicator_values[0], name='MACD'),
                      row=3, col=1)
        fig.add_trace(go.Scatter(x=data.index, y=indicator_values[1], name='Signal'),
                      row=3, col=1)
    else:
        fig.add_trace(go.Scatter(x=data.index, y=indicator_values, name=indicator),
                      row=3, col=1)
    
    fig.update_layout(height=900, title_text=f'{ticker} Backtest Results')
    st.plotly_chart(fig, use_container_width=True)
    
    # Display final profit/loss
    st.write(f'Final Profit/Loss: ${pnl[-1]:.2f}')
