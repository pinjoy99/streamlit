import streamlit as st
import pandas as pd
import plotly.express as px
import requests

# Set your Polygon.io API key
API_KEY = 'POLYGON_API_KEY'

# Function to fetch data from Polygon.io
def fetch_data(ticker):
    url = f'https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/2023-01-01/2023-12-31?apiKey={API_KEY}'
    response = requests.get(url)
    data = response.json()
    return pd.DataFrame(data['results'])

# Fetch Bullish Percent Index and SPX data
bpi_data = fetch_data('I:BPI')
spx_data = fetch_data('I:SPX')

# Streamlit app layout
st.title('Bullish Percent Index and SPX Interactive Chart')

# Plot the data using Plotly
fig = px.line(bpi_data, x='t', y='c', title='Bullish Percent Index')
fig.add_scatter(x=spx_data['t'], y=spx_data['c'], mode='lines', name='SPX')

# Display the chart in Streamlit
st.plotly_chart(fig)

# Run the Streamlit app
# Use the command: streamlit run app.py
