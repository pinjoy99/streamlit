import streamlit as st
import pandas_datareader.data as web
from datetime import datetime
import os

# Set API keys in environment variables or directly in the code (not recommended for production)
os.environ['TIINGO_API_KEY'] = 'your_tiingo_api_key'
os.environ['IEX_API_KEY'] = 'your_iex_api_key'
os.environ['ALPHAVANTAGE_API_KEY'] = 'your_alpha_vantage_api_key'
os.environ['ENIGMA_API_KEY'] = 'your_enigma_api_key'

# Define start and end dates for data retrieval
start = datetime(2020, 1, 1)
end = datetime(2020, 12, 31)

# Streamlit app title
st.title("Pandas DataReader Examples")

# Function to display data from different sources
def display_data(source, symbol):
    try:
        df = web.DataReader(symbol, source, start, end)
        st.write(f"Data from {source} for {symbol}:")
        st.dataframe(df.head())
    except Exception as e:
        st.write(f"Failed to retrieve data from {source} for {symbol}: {e}")

# Display examples for each data source
display_data('tiingo', 'GOOG')
display_data('iex', 'AAPL')
display_data('av-daily', 'MSFT')
display_data('econdb', 'ticker=RGDPUS')
display_data('quandl', 'WIKI/AAPL')
display_data('fred', 'GDP')
display_data('famafrench', '5_Industry_Portfolios')
display_data('wb', ['NY.GDP.PCAP.KD'])
display_data('oecd', 'TUD')
display_data('eurostat', 'tran_sf_railac')
display_data('tsp', None)  # No symbol needed for TSP
display_data('nasdaq-trader', None)  # No symbol needed for Nasdaq Trader
display_data('stooq', '^DJI')
display_data('moex', ['USD000UTSTOM'])
display_data('yahoo', 'GE')

# Note: For some sources like Enigma and Nasdaq Trader, additional setup or different methods might be needed.
