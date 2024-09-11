import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from polygon import RESTClient

# Initialize the Polygon API client
api_key = "DCgGFNX2zT9ir2qeZycNgr9aQ0d6JfXl"  # Replace with your actual API key
client = RESTClient(api_key)

# Fetch Bullish Percent Index data
bpi_data = client.stocks_equities_aggregates("BPI", 1, "day", "2023-01-01", "2023-12-31")
bpi_df = pd.DataFrame(bpi_data.results)

# Fetch S&P 500 Index data
spx_data = client.stocks_equities_aggregates("SPX", 1, "day", "2023-01-01", "2023-12-31")
spx_df = pd.DataFrame(spx_data.results)


# Convert timestamps to datetime
bpi_df['timestamp'] = pd.to_datetime(bpi_df['timestamp'], unit='ms')
spx_df['timestamp'] = pd.to_datetime(spx_df['timestamp'], unit='ms')

# Align data on the same date range
bpi_df.set_index('timestamp', inplace=True)
spx_df.set_index('timestamp', inplace=True)


# Create a figure with secondary y-axis
fig = make_subplots(specs=[[{"secondary_y": True}]])

# Add BPI data to the primary y-axis
fig.add_trace(
    go.Scatter(x=bpi_df.index, y=bpi_df['close'], name="Bullish Percent Index"),
    secondary_y=False,
)

# Add SPX data to the secondary y-axis
fig.add_trace(
    go.Scatter(x=spx_df.index, y=spx_df['close'], name="S&P 500 Index"),
    secondary_y=True,
)

# Add titles and labels
fig.update_layout(
    title_text="Bullish Percent Index vs S&P 500 Index",
    xaxis_title="Date",
)

fig.update_yaxes(title_text="<b>BPI</b>", secondary_y=False)
fig.update_yaxes(title_text="<b>SPX</b>", secondary_y=True)


# Display the chart in Streamlit
st.plotly_chart(fig, use_container_width=True)


