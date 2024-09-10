"""
This Streamlit app downloads multiple market sentiment indices and compares them with the SPX index in an interactive chart.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from polygon import RESTClient  # Example for SPX data, replace with your data source
import requests  # For downloading sentiment data

# Set up the Streamlit app
st.title("Market Sentiment Indices vs SPX Index")

# Function to download SPX data
def get_spx_data():
    client = RESTClient("YOUR_API_KEY")  # Replace with your API key
    aggs = client.list_aggs("I:SPX", 1, "day", "2023-01-01", "2023-12-31", limit=50000)
    spx_data = pd.DataFrame([a.__dict__ for a in aggs])
    spx_data['date'] = pd.to_datetime(spx_data['timestamp'], unit='ms')
    return spx_data[['date', 'close']]

# Function to download sentiment indices
def get_sentiment_data():
    # Example: Replace with actual API calls to download sentiment data
    response = requests.get("https://api.example.com/sentiment")
    data = response.json()
    sentiment_data = pd.DataFrame(data)
    sentiment_data['date'] = pd.to_datetime(sentiment_data['date'])
    return sentiment_data

# Load data
spx_data = get_spx_data()
sentiment_data = get_sentiment_data()

# Merge datasets on date
merged_data = pd.merge(spx_data, sentiment_data, on='date')

# Plot interactive chart
fig = px.line(merged_data, x='date', y=['close', 'sentiment_index_1', 'sentiment_index_2'], 
              labels={'value': 'Index Value', 'variable': 'Index'},
              title='Market Sentiment Indices vs SPX Index')

st.plotly_chart(fig, use_container_width=True)
