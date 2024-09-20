import streamlit as st
import pandas_datareader.data as web
from datetime import datetime
import os

# Set API keys for services that require them
os.environ['TIINGO_API_KEY'] = 'your_tiingo_api_key'
os.environ['IEX_API_KEY'] = 'your_iex_api_key'
os.environ['ALPHAVANTAGE_API_KEY'] = 'your_alpha_vantage_api_key'
os.environ['ENIGMA_API_KEY'] = 'your_enigma_api_key'

# Define the date range for historical data
start = datetime(2020, 1, 1)
end = datetime(2023, 1, 1)

# Function to load data from different sources
def load_data():
    data_sources = {
        "Tiingo": lambda: web.get_data_tiingo('GOOG', api_key=os.getenv('TIINGO_API_KEY')),
        "IEX": lambda: web.DataReader('AAPL', 'iex', start, end),
        "Alpha Vantage": lambda: web.DataReader('AAPL', 'av-daily', start=start, end=end, api_key=os.getenv('ALPHAVANTAGE_API_KEY')),
        "Econdb": lambda: web.DataReader('ticker=RGDPUS', 'econdb'),
        "Enigma": lambda: web.get_data_enigma('292129b0-1275-44c8-a6a3-2a0881f24fe1', os.getenv('ENIGMA_API_KEY')),
        "Quandl": lambda: web.DataReader('WIKI/AAPL', 'quandl', start=start, end=end),
        "FRED": lambda: web.DataReader('GDP', 'fred', start=start, end=end),
        "Fama/French": lambda: web.DataReader('5_Industry_Portfolios', 'famafrench'),
        "World Bank": lambda: web.download(indicator='NY.GDP.PCAP.KD', country=['US'], start=2005, end=2008),
        "OECD": lambda: web.DataReader('TUD', 'oecd'),
        "Eurostat": lambda: web.DataReader('tran_sf_railac', 'eurostat'),
        "Thrift Savings Plan": lambda: tsp.TSPReader(start='2020-01-01', end='2020-12-31').read(),
        "Nasdaq Trader": lambda: get_nasdaq_symbols(),
        "Stooq": lambda: web.DataReader('^DJI', 'stooq'),
        "MOEX": lambda: pdr.get_data_moex(['USD000UTSTOM'], start='2020-07-02', end='2020-07-07'),
        "Yahoo Finance": lambda: web.DataReader('AAPL', 'yahoo', start=start, end=end)
    }
    return data_sources

# Streamlit app layout
st.title("Pandas Datareader Example Data")
st.write("This app demonstrates downloading data from various sources using pandas-datareader.")

data_sources = load_data()

for source_name, data_func in data_sources.items():
    st.subheader(source_name)
    try:
        df = data_func()
        st.write(df.head())
    except Exception as e:
        st.error(f"Failed to load data from {source_name}: {e}")
