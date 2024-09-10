"""
This Streamlit app downloads multiple market sentiment indices and compares them with the SPX index in an interactive chart. The app does not use the Polygon API.
"""

import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px

# Title of the app
st.title('Market Sentiment Indices vs SPX Index')

# Function to download data
def download_data(tickers):
    data = {}
    for ticker in tickers:
        data[ticker] = yf.download(ticker, start="2020-01-01", end="2023-12-31")
    return data

# Define sentiment indices and SPX
sentiment_tickers = ['^VIX', '^NYA']  # Example tickers for sentiment indices
spx_ticker = '^GSPC'  # SPX index ticker

# Download data
data = download_data(sentiment_tickers + [spx_ticker])

# Create a DataFrame for plotting
df = pd.DataFrame({
    'Date': data[spx_ticker].index,
    'SPX': data[spx_ticker]['Close'],
    'VIX': data['^VIX']['Close'],
    'NYSE': data['^NYA']['Close']
})

# Plot interactive chart
fig = px.line(df, x='Date', y=['SPX', 'VIX', 'NYSE'], title='Market Sentiment Indices vs SPX Index')
st.plotly_chart(fig)

# Add some interactivity
st.sidebar.header('Select Indices to Display')
selected_indices = st.sidebar.multiselect('Indices', ['SPX', 'VIX', 'NYSE'], default=['SPX', 'VIX', 'NYSE'])

# Update chart based on selection
fig = px.line(df, x='Date', y=selected_indices, title='Market Sentiment Indices vs SPX Index')
st.plotly_chart(fig)
