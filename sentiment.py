"""
Streamlit App: Bullish Percent Index (BPI) vs SPX Index
This app downloads the Bullish Percent Index (BPI) and compares it with the SPX index in an interactive chart.
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import altair as alt

# Set up the Streamlit app layout
st.set_page_config(layout="wide")
st.title("Bullish Percent Index (BPI) vs SPX Index")

# Function to download data
def download_data(ticker, start, end):
    data = yf.download(ticker, start=start, end=end)
    return data['Close']

# Define the date range for data retrieval
start_date = '2020-01-01'
end_date = '2024-01-01'

# Download BPI and SPX data
bpi_data = download_data('^BPSPX', start_date, end_date)
spx_data = download_data('^GSPC', start_date, end_date)

# Combine data into a single DataFrame
data = pd.DataFrame({
    'Date': bpi_data.index,
    'BPI': bpi_data.values,
    'SPX': spx_data.values
})

# Create an interactive chart using Altair
chart = alt.Chart(data).transform_fold(
    fold=['BPI', 'SPX'],
    as_=['Index', 'Value']
).mark_line().encode(
    x='Date:T',
    y='Value:Q',
    color='Index:N'
).properties(
    width=800,
    height=400
)

# Display the chart in Streamlit
st.altair_chart(chart, use_container_width=True)

# Add a download button for the data
csv = data.to_csv(index=False)
st.download_button(
    label="Download data as CSV",
    data=csv,
    file_name='bpi_spx_data.csv',
    mime='text/csv'
)
