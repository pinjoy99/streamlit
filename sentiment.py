
import streamlit as st
import yfinance as yf
import plotly.graph_objs as go
from datetime import datetime, timedelta

# Set default values
default_tickers = ["^GSPC", "^VIX"]  # SPX and VIX
default_period = "1y"

# Streamlit app title
st.title("Stock Price Comparison App")

# Sidebar for user inputs
st.sidebar.header("User Input")
ticker1 = st.sidebar.text_input("First Ticker", value=default_tickers[0])
ticker2 = st.sidebar.text_input("Second Ticker", value=default_tickers[1])
period = st.sidebar.selectbox("Select Period", ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"], index=5)

# Download data
data1 = yf.download(ticker1, period=period)
data2 = yf.download(ticker2, period=period)

# Plotting
fig = go.Figure()

# Add first ticker to primary y-axis
fig.add_trace(go.Scatter(x=data1.index, y=data1['Close'], name=ticker1, yaxis="y1"))

# Add second ticker to secondary y-axis
fig.add_trace(go.Scatter(x=data2.index, y=data2['Close'], name=ticker2, yaxis="y2"))

# Update layout for dual y-axis
fig.update_layout(
    title=f"Stock Prices: {ticker1} vs {ticker2}",
    xaxis=dict(title="Date"),
    yaxis=dict(title=f"{ticker1} Price"),
    yaxis2=dict(title=f"{ticker2} Price", overlaying="y", side="right"),
    legend=dict(x=0, y=1),
)

# Display the chart
st.plotly_chart(fig, use_container_width=True)
