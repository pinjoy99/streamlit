import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Set default values
default_tickers = ["^GSPC", "^BPSPX"]  # SPX and BPSPX
default_period = "1y"

# Streamlit app title
st.title("Stock Data Visualization")

# Sidebar for user inputs
st.sidebar.header("User Input")
tickers = st.sidebar.text_input("Enter tickers (comma separated)", ",".join(default_tickers))
period = st.sidebar.selectbox("Select period", ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"], index=5)

# Convert user input into a list
ticker_list = [ticker.strip() for ticker in tickers.split(",")]

# Download data using yfinance
data = yf.download(ticker_list, period=period)

# Create interactive chart using Plotly
fig = go.Figure()

# Add traces for each ticker
for ticker in ticker_list:
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'][ticker], mode='lines', name=ticker))

# Add secondary y-axis
fig.update_layout(
    title="Stock Prices Over Time",
    xaxis_title="Date",
    yaxis_title="Price",
    yaxis2=dict(
        title="Secondary Axis",
        overlaying='y',
        side='right'
    )
)

# Display the chart in Streamlit
st.plotly_chart(fig)
