import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(page_title="SPX Daily Returns Analysis", layout="wide")

st.title("SPX Daily Returns Analysis")

# Download data
@st.cache_data
def download_data():
    symbol = '^GSPC'
    end_date = datetime.now()
    start_date = end_date - timedelta(days=3652)  # Approximately 10 years
    data = yf.download(symbol, start=start_date, end=end_date)
    data['Daily Return'] = data['Adj Close'].pct_change()
    return data

data = download_data()

# Display OHLC data
st.header("SPX OHLC Data")
st.dataframe(data.head())

# Histogram of daily returns
st.header("Histogram of Daily Returns")
fig_hist = go.Figure()
fig_hist.add_trace(go.Histogram(x=data['Daily Return'].dropna(), nbinsx=200, name='Daily Returns'))
fig_hist.update_layout(title='Histogram of Daily Returns for SPX', xaxis_title='Daily Returns', yaxis_title='Frequency')
st.plotly_chart(fig_hist, use_container_width=True)

# Calculate days below thresholds
st.header("Days Below Return Thresholds")
thresholds = [-0.05, -0.04, -0.03, -0.02, -0.01]
days_below = {f"{threshold*100}%": (data['Daily Return'] < threshold).sum() for threshold in thresholds}

# Display results in a table
threshold_df = pd.DataFrame.from_dict(days_below, orient='index', columns=['Number of Days'])
threshold_df.index.name = 'Threshold'
st.table(threshold_df)

# Find dates and returns below -2%
negative_returns = data[data['Daily Return'] < -0.02][['Daily Return']]
negative_returns.reset_index(inplace=True)

# Display negative returns in a chart
st.header("Daily Returns Below -2%")
fig_negative = go.Figure()
fig_negative.add_trace(go.Scatter(x=negative_returns['Date'], y=negative_returns['Daily Return'], mode='markers', name='Returns < -2%'))
fig_negative.update_layout(title='Daily Returns Below -2%', xaxis_title='Date', yaxis_title='Daily Return')
st.plotly_chart(fig_negative, use_container_width=True)

# Display negative returns in a table
st.dataframe(negative_returns)
