import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# Set your Polygon.io API key here
API_KEY = 'POLYGON_API_KEY'

# Function to get data from Polygon.io
def get_polygon_data(ticker, start_date, end_date):
    url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/{start_date}/{end_date}?apiKey={API_KEY}"
    response = requests.get(url)
    data = response.json()
    return data['results']

# Streamlit app
st.title("SPX and VIX Data Visualization")

# Date inputs
start_date = st.date_input("Start date", datetime.now() - timedelta(days=30))
end_date = st.date_input("End date", datetime.now())

# Fetch data
if st.button("Fetch Data"):
    spx_data = get_polygon_data("I:SPX", start_date, end_date)
    vix_data = get_polygon_data("I:VIX", start_date, end_date)

    # Convert to DataFrame
    spx_df = pd.DataFrame(spx_data)
    vix_df = pd.DataFrame(vix_data)

    # Convert timestamps to datetime
    spx_df['t'] = pd.to_datetime(spx_df['t'], unit='ms')
    vix_df['t'] = pd.to_datetime(vix_df['t'], unit='ms')

    # Plot data
    fig = px.line(spx_df, x='t', y='c', title='SPX Closing Prices')
    fig.add_scatter(x=vix_df['t'], y=vix_df['c'], mode='lines', name='VIX Closing Prices')
    st.plotly_chart(fig)
import os
import streamlit as st
from polygon import RESTClient
import pandas as pd
import matplotlib.pyplot as plt
import mpld3
import streamlit.components.v1 as components

# Set up the Streamlit app
st.title("Bullish Percent Index and SPX Interactive Chart")

# Input for API key
polygon_api_key = st.sidebar.text_input("Polygon API Key", type="password")

# Input for date range
start_date = st.sidebar.date_input("Start Date")
end_date = st.sidebar.date_input("End Date")

if polygon_api_key:
    # Initialize the Polygon REST client
    client = RESTClient(polygon_api_key)

    # Fetch SPX data
    spx_data = client.get_aggs("SPX", 1, "day", start_date, end_date)
    spx_df = pd.DataFrame(spx_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

    # Fetch Bullish Percent Index data
    bpi_data = client.get_aggs("VIX", 1, "day", start_date, end_date)
    bpi_df = pd.DataFrame(bpi_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

    # Plotting
    fig, ax = plt.subplots()
    ax.plot(pd.to_datetime(spx_df['timestamp'], unit='ms'), spx_df['close'], label='SPX')
    ax.plot(pd.to_datetime(bpi_df['timestamp'], unit='ms'), bpi_df['close'], label='Bullish Percent Index')
    ax.set_title('SPX and Bullish Percent Index')
    ax.set_xlabel('Date')
    ax.set_ylabel('Index Value')
    ax.legend()

    # Make the chart interactive
    fig_html = mpld3.fig_to_html(fig)
    components.html(fig_html, height=600)
else:
    st.error("Please enter your Polygon API Key.")
