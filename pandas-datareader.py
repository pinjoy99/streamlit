import streamlit as st
import pandas_datareader.data as web
from datetime import datetime
import os

# Set API keys as environment variables or use directly in the code
os.environ['TIINGO_API_KEY'] = 'YOUR_TIINGO_API_KEY'
os.environ['ALPHAVANTAGE_API_KEY'] = 'YOUR_ALPHAVANTAGE_API_KEY'
os.environ['IEX_API_KEY'] = 'YOUR_IEX_API_KEY'

# Define date range for data retrieval
start = datetime(2020, 1, 1)
end = datetime(2021, 1, 1)

# Define a function to fetch data from different sources
def fetch_data():
    data_sources = {
        "Tiingo": lambda: web.get_data_tiingo('GOOG', start=start, end=end, api_key=os.getenv('TIINGO_API_KEY')),
        "IEX": lambda: web.DataReader('AAPL', 'iex', start=start, end=end),
        "Alpha Vantage": lambda: web.DataReader('AAPL', 'av-daily', start=start, end=end, api_key=os.getenv('ALPHAVANTAGE_API_KEY')),
        "FRED": lambda: web.DataReader('GDP', 'fred', start=start, end=end),
        "World Bank": lambda: web.wb.download(indicator='NY.GDP.PCAP.KD', country=['US'], start=2019, end=2020),
        "OECD": lambda: web.DataReader('TUD', 'oecd'),
        "Eurostat": lambda: web.DataReader('tran_sf_railac', 'eurostat'),
        "Stooq": lambda: web.DataReader('^DJI', 'stooq'),
        "Yahoo Finance": lambda: web.DataReader('GE', 'yahoo', start=start, end=end)
    }

    data_frames = {}
    for source_name, fetch_func in data_sources.items():
        try:
            df = fetch_func()
            data_frames[source_name] = df.head()
        except Exception as e:
            st.error(f"Failed to fetch data from {source_name}: {e}")
    
    return data_frames

# Streamlit app layout
st.title("Pandas Datareader Example App")
st.write("This app demonstrates fetching example datasets using pandas-datareader from various sources.")

data_frames = fetch_data()

for source_name, df in data_frames.items():
    st.subheader(f"Data from {source_name}")
    st.write(df)
