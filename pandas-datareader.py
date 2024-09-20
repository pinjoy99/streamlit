import streamlit as st
import pandas_datareader.data as web
from datetime import datetime

# Set the start and end dates for data retrieval
start = datetime(2020, 1, 1)
end = datetime(2023, 1, 1)

# Define a function to fetch data from different sources
def fetch_data(source):
    if source == "Yahoo Finance":
        return web.DataReader('AAPL', 'yahoo', start, end)
    elif source == "IEX":
        return web.DataReader('AAPL', 'iex', start, end)
    elif source == "FRED":
        return web.DataReader('GDP', 'fred', start, end)
    elif source == "World Bank":
        return web.DataReader('NY.GDP.MKTP.CD', 'wb', start, end)
    elif source == "OECD":
        return web.DataReader('HUR', 'oecd', start, end)
    elif source == "Quandl":
        return web.DataReader('WIKI/AAPL', 'quandl', start, end)
    else:
        return None

# Create a Streamlit app
st.title("Pandas Datareader Examples")
st.sidebar.header("Data Source Selection")

# List of available sources
sources = ["Yahoo Finance", "IEX", "FRED", "World Bank", "OECD", "Quandl"]

# Sidebar for selecting the data source
selected_source = st.sidebar.selectbox("Select a data source:", sources)

# Fetch and display data from the selected source
data = fetch_data(selected_source)
if data is not None:
    st.write(f"Data from {selected_source}:")
    st.write(data.head())
else:
    st.write("Data source is not supported or no data available.")
