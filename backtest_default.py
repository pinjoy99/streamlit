import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from ta.trend import SMAIndicator, MACD
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange
from datetime import datetime, timedelta

st.set_page_config(layout="wide")

## Sidebar
st.sidebar.header("Stock Selection and Strategy Parameters")

# Top 30 most traded stocks and ETFs
tickers = ['AAPL', 'MSFT', 'AMZN', 'GOOGL', 'META', 'TSLA', 'NVDA', 'JPM', 'V', 'UNH', 
           'JNJ', 'WMT', 'PG', 'MA', 'HD', 'BAC', 'DIS', 'ADBE', 'CRM', 'NFLX',
           'SPY', 'QQQ', 'IWM', 'EFA', 'EEM', 'VTI', 'GLD', 'TLT', 'LQD', 'VNQ']

selected_ticker = st.sidebar.selectbox("Select a stock ticker", tickers)

end_date = datetime.now()
start_date = end_date - timedelta(days=4*365)
date_range = st.sidebar.date_input("Select date range", [start_date, end_date])

indicators = ["SMA Crossover", "MACD", "RSI", "ATR"]
selected_indicator = st.sidebar.selectbox("Select an indicator", indicators)

if selected_indicator == "SMA Crossover":
    short_window = st.sidebar.slider("Short window", 5, 50, 20)
    long_window = st.sidebar.slider("Long window", 20, 200, 50)
elif selected_indicator == "MACD":
    fast_period = st.sidebar.slider("Fast period", 5, 20, 12)
    slow_period = st.sidebar.slider("Slow period", 20, 50, 26)
    signal_period = st.sidebar.slider("Signal period", 5, 20, 9)
elif selected_indicator == "RSI":
    rsi_period = st.sidebar.slider("RSI period", 5, 30, 14)
    rsi_overbought = st.sidebar.slider("Overbought level", 70, 90, 70)
    rsi_oversold = st.sidebar.slider("Oversold level", 10, 30, 30)
elif selected_indicator == "ATR":
    atr_period = st.sidebar.slider("ATR period", 5, 30, 14)
    atr_multiplier = st.sidebar.slider("ATR multiplier", 1.0, 5.0, 2.0, 0.1)

## Main content
st.title(f"Stock Analysis and Backtesting: {selected_ticker}")

@st.cache_data
def load_data(ticker, start, end):
    data = yf.download(ticker, start=start, end=end)
    return data

data = load_data(selected_ticker, date_range[0], date_range[1])

if data.empty:
    st.error("No data available for the selected stock and date range.")
else:
    st.subheader("Historical Data")
    st.dataframe(data.head())

    csv = data.to_csv().encode('utf-8')
    st.download_button(
        label="Download CSV",
        data=csv,
        file_name=f"{selected_ticker}_historical_data.csv",
        mime="text/csv",
    )

    # Calculate indicator and generate signals
    if selected_indicator == "SMA Crossover":
        data['SMA_short'] = SMAIndicator(data['Close'], window=short_window).sma_indicator()
        data['SMA_long'] = SMAIndicator(data['Close'], window=long_window).sma_indicator()
        data['Signal'] = np.where(data['SMA_short'] > data['SMA_long'], 1, 0)
        data['Position'] = data['Signal'].diff()
    elif selected_indicator == "MACD":
        macd = MACD(data['Close'], fast_period, slow_period, signal_period)
        data['MACD'] = macd.macd()
        data['Signal_line'] = macd.macd_signal()
        data['Signal'] = np.where(data['MACD'] > data['Signal_line'], 1, 0)
        data['Position'] = data['Signal'].diff()
    elif selected_indicator == "RSI":
        data['RSI'] = RSIIndicator(data['Close'], window=rsi_period).rsi()
        data['Signal'] = np.where(data['RSI'] < rsi_oversold, 1, np.where(data['RSI'] > rsi_overbought, 0, np.nan))
        data['Signal'] = data['Signal'].ffill()
        data['Position'] = data['Signal'].diff()
    elif selected_indicator == "ATR":
        data['ATR'] = AverageTrueRange(data['High'], data['Low'], data['Close'], window=atr_period).average_true_range()
        data['Upper_Band'] = data['Close'] + atr_multiplier * data['ATR']
        data['Lower_Band'] = data['Close'] - atr_multiplier * data['ATR']
        data['Signal'] = np.where(data['Close'] > data['Upper_Band'].shift(1), 0, 
                                  np.where(data['Close'] < data['Lower_Band'].shift(1), 1, np.nan))
        data['Signal'] = data['Signal'].ffill()
        data['Position'] = data['Signal'].diff()

    # Calculate returns
    data['Strategy_Returns'] = data['Close'].pct_change() * data['Signal'].shift(1)
    data['Cumulative_Strategy_Returns'] = (1 + data['Strategy_Returns']).cumprod()
    data['Buy_and_Hold_Returns'] = (1 + data['Close'].pct_change()).cumprod()

    # Create interactive plot
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.05, 
                        subplot_titles=("Stock Price", "Strategy Performance", "Indicator"))

    # Stock price chart
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'], name="Close Price"), row=1, col=1)
    fig.add_trace(go.Scatter(x=data[data['Position'] == 1].index, 
                             y=data[data['Position'] == 1]['Close'],
                             mode='markers', name='Buy Signal', marker=dict(symbol='triangle-up', size=10, color='green')), row=1, col=1)
    fig.add_trace(go.Scatter(x=data[data['Position'] == -1].index, 
                             y=data[data['Position'] == -1]['Close'],
                             mode='markers', name='Sell Signal', marker=dict(symbol='triangle-down', size=10, color='red')), row=1, col=1)

    # Performance chart
    fig.add_trace(go.Scatter(x=data.index, y=data['Cumulative_Strategy_Returns'], name="Strategy Returns"), row=2, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data['Buy_and_Hold_Returns'], name="Buy and Hold Returns"), row=2, col=1)

    # Indicator chart
    if selected_indicator == "SMA Crossover":
        fig.add_trace(go.Scatter(x=data.index, y=data['SMA_short'], name=f"SMA {short_window}"), row=3, col=1)
        fig.add_trace(go.Scatter(x=data.index, y=data['SMA_long'], name=f"SMA {long_window}"), row=3, col=1)
    elif selected_indicator == "MACD":
        fig.add_trace(go.Scatter(x=data.index, y=data['MACD'], name="MACD"), row=3, col=1)
        fig.add_trace(go.Scatter(x=data.index, y=data['Signal_line'], name="Signal Line"), row=3, col=1)
    elif selected_indicator == "RSI":
        fig.add_trace(go.Scatter(x=data.index, y=data['RSI'], name="RSI"), row=3, col=1)
        fig.add_hline(y=rsi_overbought, line_dash="dash", line_color="red", row=3, col=1)
        fig.add_hline(y=rsi_oversold, line_dash="dash", line_color="green", row=3, col=1)
    elif selected_indicator == "ATR":
        fig.add_trace(go.Scatter(x=data.index, y=data['Upper_Band'], name="Upper Band"), row=3, col=1)
        fig.add_trace(go.Scatter(x=data.index, y=data['Lower_Band'], name="Lower Band"), row=3, col=1)
        fig.add_trace(go.Scatter(x=data.index, y=data['Close'], name="Close Price"), row=3, col=1)

    fig.update_layout(height=900, width=1000, title_text="Stock Analysis and Strategy Performance")
    st.plotly_chart(fig)

    # Trade details
    trades = data[data['Position'] != 0].copy()
    trades['Trade_Type'] = np.where(trades['Position'] == 1, 'Buy', 'Sell')
    trades['Holding_Period'] = trades.index.to_series().diff().dt.days
    trades['Proceeds'] = trades['Close'] * trades['Position'] * -1
    trades['Cumulative_Profit_Loss'] = trades['Proceeds'].cumsum()

    st.subheader("Trade Details")
    st.dataframe(trades[['Trade_Type', 'Close', 'Holding_Period', 'Proceeds', 'Cumulative_Profit_Loss']])

    # Strategy metrics
    total_return = data['Cumulative_Strategy_Returns'].iloc[-1] - 1
    buy_hold_return = data['Buy_and_Hold_Returns'].iloc[-1] - 1
    trading_days = (data.index[-1] - data.index[0]).days / 365.25
    cagr = (1 + total_return) ** (1 / trading_days) - 1
    mdd = (data['Cumulative_Strategy_Returns'] / data['Cumulative_Strategy_Returns'].cummax() - 1).min()
    max_loss_per_trade = trades['Proceeds'].min()
    loss_rate = len(trades[trades['Proceeds'] < 0]) / len(trades)

    st.subheader("Strategy Metrics")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Return", f"{total_return:.2%}")
    col1.metric("Buy & Hold Return", f"{buy_hold_return:.2%}")
    col2.metric("CAGR", f"{cagr:.2%}")
    col2.metric("Max Drawdown", f"{mdd:.2%}")
    col3.metric("Max Loss per Trade", f"${max_loss_per_trade:.2f}")
    col3.metric("Loss Rate", f"{loss_rate:.2%}")
