# """
# Create a streamlit app that
# downloads historical data of a chosen stock ticker among top 30 most traded stocks and ETFs for a chosen time range (default 4 years) shown in the side bar,

# backtests long-only stock trading strategies 
# based on a chosen indicator and parameters shown in the side bar among top-10 most popular TA indicators including but not limited to SMA crossover, MACD, RSI, ATR using ta package,

# presents an interactive plot of a subplot showing stock-price line chart with buy/sell markers, a subplot showing gain/loss chart as well as a benchmark of buy-and-hold , and a subplot showing the indicator chart with buy/sell signals,

# creates a table showing the details of individual trades including holding positions, proceeds per trade and a cumulative profit/loss.

# includes the metrics to compare the chosen strategy with the Buy & Hold including total return, CAGR, MDD, Max Loss, Win rate, etc.
# """

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from ta import add_all_ta_features
from ta.utils import dropna
from datetime import datetime, timedelta

# Define top 30 most traded stocks and ETFs
top_tickers = ['AAPL', 'MSFT', 'AMZN', 'GOOGL', 'FB', 'TSLA', 'NVDA', 'JPM', 'JNJ', 'V', 
               'PG', 'UNH', 'HD', 'MA', 'DIS', 'PYPL', 'BAC', 'ADBE', 'CMCSA', 'XOM',
               'SPY', 'QQQ', 'IWM', 'EFA', 'EEM', 'VTI', 'VEA', 'VWO', 'BND', 'AGG']

# Sidebar inputs
st.sidebar.header('Input Parameters')
ticker = st.sidebar.selectbox('Select Stock Ticker', top_tickers)
end_date = datetime.now().date()
start_date = st.sidebar.date_input('Start Date', end_date - timedelta(days=4*365))
indicator = st.sidebar.selectbox('Select Indicator', ['SMA', 'EMA', 'MACD', 'RSI', 'ATR', 'Bollinger Bands', 'Stochastic', 'CCI', 'MFI', 'OBV'])

# Indicator parameters
if indicator in ['SMA', 'EMA']:
    fast_period = st.sidebar.slider('Fast Period', 5, 50, 20)
    slow_period = st.sidebar.slider('Slow Period', 10, 200, 50)
elif indicator == 'MACD':
    fast_period = st.sidebar.slider('Fast Period', 5, 50, 12)
    slow_period = st.sidebar.slider('Slow Period', 10, 100, 26)
    signal_period = st.sidebar.slider('Signal Period', 5, 20, 9)
elif indicator in ['RSI', 'CCI', 'MFI']:
    period = st.sidebar.slider('Period', 5, 30, 14)
    overbought = st.sidebar.slider('Overbought Level', 60, 90, 70)
    oversold = st.sidebar.slider('Oversold Level', 10, 40, 30)
elif indicator == 'ATR':
    period = st.sidebar.slider('Period', 5, 30, 14)
    multiplier = st.sidebar.slider('Multiplier', 1.0, 5.0, 2.0, 0.1)
elif indicator == 'Bollinger Bands':
    period = st.sidebar.slider('Period', 5, 50, 20)
    std_dev = st.sidebar.slider('Standard Deviation', 1.0, 3.0, 2.0, 0.1)
elif indicator == 'Stochastic':
    k_period = st.sidebar.slider('K Period', 5, 30, 14)
    d_period = st.sidebar.slider('D Period', 1, 10, 3)
    overbought = st.sidebar.slider('Overbought Level', 60, 90, 80)
    oversold = st.sidebar.slider('Oversold Level', 10, 40, 20)
elif indicator == 'OBV':
    threshold = st.sidebar.slider('Threshold', 0, 1000000, 100000)

# Download data
@st.cache_data
def download_data(ticker, start_date, end_date):
    data = yf.download(ticker, start=start_date, end=end_date)
    return data

data = download_data(ticker, start_date, end_date)

# Calculate indicators
df = dropna(data)
df = add_all_ta_features(df, open="Open", high="High", low="Low", close="Close", volume="Volume")

# Define trading signals
def get_signal(row):
    if indicator == 'SMA':
        if row[f'trend_sma_{fast_period}'] > row[f'trend_sma_{slow_period}']:
            return 1
        else:
            return 0
    elif indicator == 'EMA':
        if row[f'trend_ema_{fast_period}'] > row[f'trend_ema_{slow_period}']:
            return 1
        else:
            return 0
    elif indicator == 'MACD':
        if row['trend_macd_diff'] > 0:
            return 1
        else:
            return 0
    elif indicator in ['RSI', 'CCI', 'MFI']:
        if row[f'momentum_{indicator.lower()}'] < oversold:
            return 1
        elif row[f'momentum_{indicator.lower()}'] > overbought:
            return 0
        else:
            return np.nan
    elif indicator == 'ATR':
        if row['Close'] > row['Close'].shift(1) + multiplier * row[f'volatility_atr_{period}']:
            return 1
        elif row['Close'] < row['Close'].shift(1) - multiplier * row[f'volatility_atr_{period}']:
            return 0
        else:
            return np.nan
    elif indicator == 'Bollinger Bands':
        if row['Close'] < row[f'volatility_bbm_{period}_{std_dev}']:
            return 1
        elif row['Close'] > row[f'volatility_bbh_{period}_{std_dev}']:
            return 0
        else:
            return np.nan
    elif indicator == 'Stochastic':
        if row[f'momentum_stoch_{k_period}_{d_period}_d'] < oversold:
            return 1
        elif row[f'momentum_stoch_{k_period}_{d_period}_d'] > overbought:
            return 0
        else:
            return np.nan
    elif indicator == 'OBV':
        if row['volume_obv'] > threshold:
            return 1
        elif row['volume_obv'] < -threshold:
            return 0
        else:
            return np.nan

df['Signal'] = df.apply(get_signal, axis=1)
df['Position'] = df['Signal'].fillna(method='ffill')

# Calculate returns
df['Strategy_Returns'] = df['Close'].pct_change() * df['Position'].shift(1)
df['Buy_Hold_Returns'] = df['Close'].pct_change()

# Calculate cumulative returns
df['Cumulative_Strategy_Returns'] = (1 + df['Strategy_Returns']).cumprod()
df['Cumulative_Buy_Hold_Returns'] = (1 + df['Buy_Hold_Returns']).cumprod()

# Create interactive plot
fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.05, 
                    subplot_titles=('Stock Price', 'Cumulative Returns', 'Indicator'))

# Stock price subplot
fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name='Close Price'), row=1, col=1)
fig.add_trace(go.Scatter(x=df[df['Signal'] == 1].index, y=df[df['Signal'] == 1]['Close'], 
                         mode='markers', name='Buy Signal', marker=dict(color='green', symbol='triangle-up', size=10)), row=1, col=1)
fig.add_trace(go.Scatter(x=df[df['Signal'] == 0].index, y=df[df['Signal'] == 0]['Close'], 
                         mode='markers', name='Sell Signal', marker=dict(color='red', symbol='triangle-down', size=10)), row=1, col=1)

# Cumulative returns subplot
fig.add_trace(go.Scatter(x=df.index, y=df['Cumulative_Strategy_Returns'], name='Strategy Returns'), row=2, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df['Cumulative_Buy_Hold_Returns'], name='Buy & Hold Returns'), row=2, col=1)

# Indicator subplot
if indicator in ['SMA', 'EMA']:
    fig.add_trace(go.Scatter(x=df.index, y=df[f'trend_{indicator.lower()}_{fast_period}'], name=f'{indicator} {fast_period}'), row=3, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df[f'trend_{indicator.lower()}_{slow_period}'], name=f'{indicator} {slow_period}'), row=3, col=1)
elif indicator == 'MACD':
    fig.add_trace(go.Scatter(x=df.index, y=df['trend_macd'], name='MACD'), row=3, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['trend_macd_signal'], name='Signal'), row=3, col=1)
    fig.add_bar(x=df.index, y=df['trend_macd_diff'], name='MACD Histogram', row=3, col=1)
elif indicator in ['RSI', 'CCI', 'MFI']:
    fig.add_trace(go.Scatter(x=df.index, y=df[f'momentum_{indicator.lower()}'], name=indicator), row=3, col=1)
    fig.add_hline(y=overbought, line_dash="dash", line_color="red", row=3, col=1)
    fig.add_hline(y=oversold, line_dash="dash", line_color="green", row=3, col=1)
elif indicator == 'ATR':
    fig.add_trace(go.Scatter(x=df.index, y=df[f'volatility_atr_{period}'], name='ATR'), row=3, col=1)
elif indicator == 'Bollinger Bands':
    fig.add_trace(go.Scatter(x=df.index, y=df[f'volatility_bbm_{period}_{std_dev}'], name='Middle Band'), row=3, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df[f'volatility_bbh_{period}_{std_dev}'], name='Upper Band'), row=3, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df[f'volatility_bbl_{period}_{std_dev}'], name='Lower Band'), row=3, col=1)
elif indicator == 'Stochastic':
    fig.add_trace(go.Scatter(x=df.index, y=df[f'momentum_stoch_{k_period}_{d_period}_k'], name='%K'), row=3, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df[f'momentum_stoch_{k_period}_{d_period}_d'], name='%D'), row=3, col=1)
    fig.add_hline(y=overbought, line_dash="dash", line_color="red", row=3, col=1)
    fig.add_hline(y=oversold, line_dash="dash", line_color="green", row=3, col=1)
elif indicator == 'OBV':
    fig.add_trace(go.Scatter(x=df.index, y=df['volume_obv'], name='OBV'), row=3, col=1)
    fig.add_hline(y=threshold, line_dash="dash", line_color="red", row=3, col=1)
    fig.add_hline(y=-threshold, line_dash="dash", line_color="green", row=3, col=1)

fig.update_layout(height=900, title_text=f"{ticker} Stock Analysis")
st.plotly_chart(fig, use_container_width=True)

# Create trade details table
trades = df[df['Signal'].notnull()].copy()
trades['Trade_Type'] = trades['Signal'].map({1: 'Buy', 0: 'Sell'})
trades['Price'] = trades['Close']
trades['Holding_Period'] = (trades.index - trades.index.shift(1)).days
trades['Profit_Loss'] = trades['Close'].pct_change()
trades['Cumulative_Profit_Loss'] = (1 + trades['Profit_Loss']).cumprod() - 1

st.subheader('Trade Details')
st.dataframe(trades[['Trade_Type', 'Price', 'Holding_Period', 'Profit_Loss', 'Cumulative_Profit_Loss']])

# Calculate performance metrics
total_return_strategy = df['Cumulative_Strategy_Returns'].iloc[-1] - 1
total_return_buy_hold = df['Cumulative_Buy_Hold_Returns'].iloc[-1] - 1
cagr_strategy = (df['Cumulative_Strategy_Returns'].iloc[-1] ** (365 / len(df)) - 1) * 100
cagr_buy_hold = (df['Cumulative_Buy_Hold_Returns'].iloc[-1] ** (365 / len(df)) - 1) * 100
mdd_strategy = (df['Cumulative_Strategy_Returns'] / df['Cumulative_Strategy_Returns'].cummax() - 1).min() * 100
mdd_buy_hold = (df['Cumulative_Buy_Hold_Returns'] / df['Cumulative_Buy_Hold_Returns'].cummax() - 1).min() * 100
max_loss_strategy = df['Strategy_Returns'].min() * 100
max_loss_buy_hold = df['Buy_Hold_Returns'].min() * 100
win_rate = (df['Strategy_Returns'] > 0).mean() * 100

st.subheader('Performance Metrics')
metrics = pd.DataFrame({
    'Metric': ['Total Return (%)', 'CAGR (%)', 'Max Drawdown (%)', 'Max Loss (%)', 'Win Rate (%)'],
    'Strategy': [total_return_strategy*100, cagr_strategy, mdd_strategy, max_loss_strategy, win_rate],
    'Buy & Hold': [total_return_buy_hold*100, cagr_buy_hold, mdd_buy_hold, max_loss_buy_hold, '-']
})
st.dataframe(metrics.set_index('Metric'))
