import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

# Set page title
st.set_page_config(page_title="S&P 500 Analysis", layout="wide")

# Title
st.title("S&P 500 (SPX) 10-Year Analysis")

# Download data
@st.cache_data
def get_data():
    end_date = datetime.now()
    start_date = end_date - timedelta(days=3650)  # Approximately 10 years
    data = yf.download("^GSPC", start=start_date, end=end_date)
    return data

data = get_data()

# Calculate daily returns
data['Daily_Return'] = data['Adj Close'].pct_change()

# Display OHLC data
st.header("OHLC Data")
st.dataframe(data)

# Interactive OHLC chart
st.header("Interactive OHLC Chart")
fig = go.Figure(data=[go.Candlestick(x=data.index,
                open=data['Open'],
                high=data['High'],
                low=data['Low'],
                close=data['Close'])])
fig.update_layout(title="S&P 500 OHLC Chart", xaxis_rangeslider_visible=False)
st.plotly_chart(fig, use_container_width=True)

# Histogram of daily returns
st.header("Distribution of Daily Returns")
fig_hist = px.histogram(data, x='Daily_Return', nbins=100)
fig_hist.update_layout(title="Histogram of Daily Returns", xaxis_title="Daily Return", yaxis_title="Frequency")
st.plotly_chart(fig_hist, use_container_width=True)

# Calculate number of days below thresholds
thresholds = [-0.05, -0.04, -0.03, -0.02, -0.01]
days_below_threshold = {f"Below {threshold*100}%": (data['Daily_Return'] < threshold).sum() for threshold in thresholds}

# Display results in a table
st.header("Number of Days Below Thresholds")
threshold_df = pd.DataFrame.from_dict(days_below_threshold, orient='index', columns=['Count'])
st.table(threshold_df)

# Interactive line chart of daily returns
st.header("Daily Returns Over Time")
fig_line = px.line(data, x=data.index, y='Daily_Return')
fig_line.update_layout(title="Daily Returns", xaxis_title="Date", yaxis_title="Daily Return")
st.plotly_chart(fig_line, use_container_width=True)

# Summary statistics
st.header("Summary Statistics of Daily Returns")
summary_stats = data['Daily_Return'].describe()
st.table(summary_stats)
