import streamlit as st
import pandas_datareader.data as web
from datetime import datetime

# Set up the Streamlit app
st.title("Data Download Examples with Pandas Datareader")

# Define the date range for data retrieval
start = datetime(2020, 1, 1)
end = datetime(2023, 1, 1)

# Function to display data from a specific source
def display_data(source_name, data):
    st.subheader(source_name)
    st.write(data.head())

# Tiingo
try:
    tiingo_data = web.get_data_tiingo('AAPL', api_key='YOUR_TIINGO_API_KEY', start=start, end=end)
    display_data("Tiingo", tiingo_data)
except Exception as e:
    st.error(f"Tiingo: {e}")

# IEX
try:
    iex_data = web.DataReader('AAPL', 'iex', start, end)
    display_data("IEX", iex_data)
except Exception as e:
    st.error(f"IEX: {e}")

# Alpha Vantage
try:
    alpha_vantage_data = web.get_data_alphavantage('AAPL', api_key='YOUR_ALPHA_VANTAGE_API_KEY')
    display_data("Alpha Vantage", alpha_vantage_data)
except Exception as e:
    st.error(f"Alpha Vantage: {e}")

# Econdb
try:
    econdb_data = web.get_data_econdb('USGDP', start=start, end=end)
    display_data("Econdb", econdb_data)
except Exception as e:
    st.error(f"Econdb: {e}")

# Enigma (Note: Enigma is no longer supported in recent versions)
st.warning("Enigma support has been deprecated.")

# Quandl
try:
    quandl_data = web.get_data_quandl('WIKI/AAPL', api_key='YOUR_QUANDL_API_KEY')
    display_data("Quandl", quandl_data)
except Exception as e:
    st.error(f"Quandl: {e}")

# St. Louis FED (FRED)
try:
    fred_data = web.DataReader('GDP', 'fred', start, end)
    display_data("St. Louis FED (FRED)", fred_data)
except Exception as e:
    st.error(f"St. Louis FED (FRED): {e}")

# Kenneth French’s data library
try:
    french_data = web.DataReader('F-F_Research_Data_Factors', 'famafrench')
    display_data("Kenneth French’s Data Library", french_data[0])
except Exception as e:
    st.error(f"Kenneth French’s Data Library: {e}")

# World Bank
try:
    world_bank_data = web.get_data_wb(indicator='NY.GDP.MKTP.CD', country='USA', start=start.year, end=end.year)
    display_data("World Bank", world_bank_data)
except Exception as e:
    st.error(f"World Bank: {e}")

# OECD
try:
    oecd_data = web.get_oecd('MEI_CLI', 'USA')
    display_data("OECD", oecd_data)
except Exception as e:
    st.error(f"OECD: {e}")

# Eurostat (Note: Eurostat is not directly supported by pandas-datareader)
st.warning("Eurostat is not directly supported by pandas-datareader.")

# Thrift Savings Plan (Note: Not directly supported by pandas-datareader)
st.warning("Thrift Savings Plan is not directly supported by pandas-datareader.")

# Nasdaq Trader symbol definitions (Note: Not directly supported by pandas-datareader)
st.warning("Nasdaq Trader symbol definitions are not directly supported by pandas-datareader.")

# Stooq
try:
    stooq_data = web.DataReader('AAPL.US', 'stooq')
    display_data("Stooq", stooq_data)
except Exception as e:
    st.error(f"Stooq: {e}")

# MOEX (Moscow Exchange)
try:
    moex_data = web.DataReader('GAZP', 'moex')
    display_data("MOEX", moex_data)
except Exception as e:
    st.error(f"MOEX: {e}")

# Naver Finance (Note: Naver Finance is not directly supported by pandas-datareader)
st.warning("Naver Finance is not directly supported by pandas-datareader.")

# Yahoo Finance
try:
    yahoo_finance_data = web.DataReader('AAPL', 'yahoo', start, end)
    display_data("Yahoo Finance", yahoo_finance_data)
except Exception as e:
    st.error(f"Yahoo Finance: {e}")
