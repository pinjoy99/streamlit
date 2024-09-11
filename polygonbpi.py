import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# Set your Polygon.io API key here
API_KEY = 'DCgGFNX2zT9ir2qeZycNgr9aQ0d6JfXl'

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
