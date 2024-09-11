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
