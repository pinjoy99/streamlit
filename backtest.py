import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from ta import add_all_ta_features
from datetime import datetime, timedelta

# Define the list of top 20 most traded stocks and ETFs
top_tickers = [
    "NVDA", "TSLA", "TSM", "SOXL", "NVDL", "TQQQ", "AAPL", "AMD", "SMCI", "MSFT",
    "SQQQ", "PLTR", "TSLL", "QQQ", "AVGO", "SOXS", "ARM", "MU", "VOO", "AMZN"
]

# Sidebar inputs
st.sidebar.header("Settings")
ticker = st.sidebar.selectbox("Select a stock/ETF", top_tickers)
end_date = datetime.now().date()
start_date = st.sidebar.date_input("Start Date", end_date - timedelta(days=4*365))
end_date = st.sidebar.date_input("End Date", end_date)

# Technical indicator selection
indicator = st.sidebar.selectbox("Select Technical Indicator", ["MACD", "RSI", "ATR"])

# Indicator parameters
if indicator == "MACD":
    fast_period = st.sidebar.slider("Fast Period", 5, 50, 12)
    slow_period = st.sidebar.slider("Slow Period", 10, 100, 26)
    signal_period = st.sidebar.slider("Signal Period", 5, 20, 9)
elif indicator == "RSI":
    rsi_period = st.sidebar.slider("RSI Period", 5, 30, 14)
    overbought = st.sidebar.slider("Overbought Level", 70, 90, 70)
    oversold = st.sidebar.slider("Oversold Level", 10, 30, 30)
elif indicator == "ATR":
    atr_period = st.sidebar.slider("ATR Period", 5, 30, 14)
    atr_multiplier = st.sidebar.slider("ATR Multiplier", 1.0, 5.0, 2.0, 0.1)

# Download data
@st.cache_data
def download_data(ticker, start_date, end_date):
    data = yf.download(ticker, start=start_date, end=end_date)
    return data

data = download_data(ticker, start_date, end_date)

# Add technical indicators
data = add_all_ta_features(data, open="Open", high="High", low="Low", close="Close", volume="Volume")

# Define trading strategy
def generate_signals(data, indicator):
    signals = pd.DataFrame(index=data.index)
    signals['Signal'] = 0

    if indicator == "MACD":
        signals['Signal'] = np.where(data[f'trend_macd_diff_{fast_period}_{slow_period}_{signal_period}'] > 0, 1, 0)
    elif indicator == "RSI":
        signals['Signal'] = np.where(data[f'momentum_rsi_{rsi_period}'] < oversold, 1, 0)
        signals['Signal'] = np.where(data[f'momentum_rsi_{rsi_period}'] > overbought, 0, signals['Signal'])
    elif indicator == "ATR":
        signals['Signal'] = np.where(data['Close'] > data['Close'].shift(1) + data[f'volatility_atr_{atr_period}'] * atr_multiplier, 1, 0)
        signals['Signal'] = np.where(data['Close'] < data['Close'].shift(1) - data[f'volatility_atr_{atr_period}'] * atr_multiplier, 0, signals['Signal'])

    return signals

signals = generate_signals(data, indicator)

# Backtest strategy
def backtest_strategy(data, signals):
    portfolio = pd.DataFrame(index=signals.index)
    portfolio['Holdings'] = signals['Signal'].shift(1)
    portfolio['Close'] = data['Close']
    portfolio['Returns'] = portfolio['Close'].pct_change()
    portfolio['Strategy'] = portfolio['Holdings'] * portfolio['Returns']
    
    portfolio['Cumulative_Returns'] = (1 + portfolio['Strategy']).cumprod()
    portfolio['Benchmark'] = (1 + portfolio['Returns']).cumprod()
    
    return portfolio

portfolio = backtest_strategy(data, signals)

# Generate trade list
def generate_trade_list(portfolio):
    trades = pd.DataFrame(columns=['Entry Date', 'Exit Date', 'Entry Price', 'Exit Price', 'Shares', 'Profit/Loss', 'Cumulative P/L'])
    
    in_position = False
    entry_date = None
    entry_price = None
    shares = 0
    cumulative_pl = 0
    
    for date, row in portfolio.iterrows():
        if not in_position and row['Holdings'] == 1:
            in_position = True
            entry_date = date
            entry_price = row['Close']
            shares = 1000 / entry_price  # Assuming $1000 investment per trade
        elif in_position and row['Holdings'] == 0:
            in_position = False
            exit_date = date
            exit_price = row['Close']
            pl = (exit_price - entry_price) * shares
            cumulative_pl += pl
            trades = trades.append({
                'Entry Date': entry_date,
                'Exit Date': exit_date,
                'Entry Price': entry_price,
                'Exit Price': exit_price,
                'Shares': shares,
                'Profit/Loss': pl,
                'Cumulative P/L': cumulative_pl
            }, ignore_index=True)
    
    return trades

trades = generate_trade_list(portfolio)

# Create interactive plot
def create_plot(data, portfolio, signals, indicator):
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.5, 0.3, 0.2])
    
    # Stock price chart with buy/sell markers
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'], name='Close Price'), row=1, col=1)
    fig.add_trace(go.Scatter(x=signals[signals['Signal'] == 1].index, y=data.loc[signals['Signal'] == 1, 'Close'],
                             mode='markers', name='Buy Signal', marker=dict(symbol='triangle-up', size=10, color='green')), row=1, col=1)
    fig.add_trace(go.Scatter(x=signals[signals['Signal'] == 0].index, y=data.loc[signals['Signal'] == 0, 'Close'],
                             mode='markers', name='Sell Signal', marker=dict(symbol='triangle-down', size=10, color='red')), row=1, col=1)
    
    # Cumulative returns chart
    fig.add_trace(go.Scatter(x=portfolio.index, y=portfolio['Cumulative_Returns'], name='Strategy Returns'), row=2, col=1)
    fig.add_trace(go.Scatter(x=portfolio.index, y=portfolio['Benchmark'], name='Buy and Hold'), row=2, col=1)
    
    # Indicator chart
    if indicator == "MACD":
        fig.add_trace(go.Scatter(x=data.index, y=data[f'trend_macd_{fast_period}_{slow_period}_{signal_period}'], name='MACD'), row=3, col=1)
        fig.add_trace(go.Scatter(x=data.index, y=data[f'trend_macd_signal_{fast_period}_{slow_period}_{signal_period}'], name='Signal'), row=3, col=1)
        fig.add_bar(x=data.index, y=data[f'trend_macd_diff_{fast_period}_{slow_period}_{signal_period}'], name='MACD Histogram', row=3, col=1)
    elif indicator == "RSI":
        fig.add_trace(go.Scatter(x=data.index, y=data[f'momentum_rsi_{rsi_period}'], name='RSI'), row=3, col=1)
        fig.add_hline(y=overbought, line_dash="dash", line_color="red", row=3, col=1)
        fig.add_hline(y=oversold, line_dash="dash", line_color="green", row=3, col=1)
    elif indicator == "ATR":
        fig.add_trace(go.Scatter(x=data.index, y=data[f'volatility_atr_{atr_period}'], name='ATR'), row=3, col=1)
    
    fig.update_layout(height=800, title_text=f"{ticker} - {indicator} Strategy Backtest")
    fig.update_xaxes(title_text="Date", row=3, col=1)
    fig.update_yaxes(title_text="Price", row=1, col=1)
    fig.update_yaxes(title_text="Cumulative Returns", row=2, col=1)
    fig.update_yaxes(title_text=indicator, row=3, col=1)
    
    return fig

# Display results
st.title(f"{ticker} - {indicator} Strategy Backtest")

fig = create_plot(data, portfolio, signals, indicator)
st.plotly_chart(fig, use_container_width=True)

st.subheader("Trade List")
st.dataframe(trades)

st.subheader("Performance Metrics")
total_return = portfolio['Cumulative_Returns'].iloc[-1] - 1
benchmark_return = portfolio['Benchmark'].iloc[-1] - 1
st.write(f"Total Return: {total_return:.2%}")
st.write(f"Benchmark Return: {benchmark_return:.2%}")
st.write(f"Alpha: {total_return - benchmark_return:.2%}")
