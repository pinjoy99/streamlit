import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

st.set_page_config(layout="wide")

st.title("S&P 500 (SPX) Data Analysis")

## Data Download and Processing

end_date = datetime.now()
start_date = end_date - timedelta(days=3650)  # Approximately 10 years

@st.cache_data
def load_data():
    spx_data = yf.download("^GSPC", start=start_date, end=end_date)
    spx_data['Daily_Return'] = spx_data['Close'].pct_change()
    return spx_data

data = load_data()

## OHLC Chart

st.header("S&P 500 OHLC Chart")

fig_ohlc = go.Figure(data=[go.Candlestick(x=data.index,
                open=data['Open'],
                high=data['High'],
                low=data['Low'],
                close=data['Close'])])

fig_ohlc.update_layout(xaxis_rangeslider_visible=False)
st.plotly_chart(fig_ohlc, use_container_width=True)

## Data Table

st.header("S&P 500 Data Table")

st.dataframe(data)

## Download Button

csv = data.to_csv().encode('utf-8')
st.download_button(
    label="Download S&P 500 Data as CSV",
    data=csv,
    file_name="spx_data.csv",
    mime="text/csv",
)

## Daily Returns Histogram

st.header("Distribution of Daily Returns")

fig_hist = px.histogram(data, x='Daily_Return', nbins=50)
fig_hist.update_layout(bargap=0.1)
st.plotly_chart(fig_hist, use_container_width=True)

## Summary Statistics

st.header("Summary Statistics")

summary_stats = data['Daily_Return'].describe()
st.table(summary_stats)
