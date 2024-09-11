import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import mpld3
import streamlit.components.v1 as components

# Polygon.io API Key
API_KEY = 'DCgGFNX2zT9ir2qeZycNgr9aQ0d6JfXl'

# Function to fetch data from Polygon.io
def fetch_data(ticker, multiplier, timespan, from_date, to_date):
    url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/{multiplier}/{timespan}/{from_date}/{to_date}"
    params = {
        "apiKey": API_KEY
    }
    response = requests.get(url, params=params)
    data = response.json()
    return pd.DataFrame(data['results'])

# Fetch Bullish Percent Index and SPX data
bpi_data = fetch_data("INDEX/BPI", 1, "day", "2023-01-01", "2023-12-31")
spx_data = fetch_data("INDEX/SPX", 1, "day", "2023-01-01", "2023-12-31")

# Convert timestamps to datetime
bpi_data['timestamp'] = pd.to_datetime(bpi_data['t'], unit='ms')
spx_data['timestamp'] = pd.to_datetime(spx_data['t'], unit='ms')

# Plotting
fig, ax = plt.subplots()
ax.plot(bpi_data['timestamp'], bpi_data['c'], label='Bullish Percent Index')
ax.plot(spx_data['timestamp'], spx_data['c'], label='SPX')
ax.set_title('Bullish Percent Index and SPX')
ax.set_xlabel('Date')
ax.set_ylabel('Value')
ax.legend()

# Convert the Matplotlib figure to HTML using mpld3
fig_html = mpld3.fig_to_html(fig)

# Display the interactive chart in Streamlit
components.html(fig_html, height=600)

# Run the app
if __name__ == "__main__":
    st.title("Bullish Percent Index and SPX Interactive Chart")
    st.write("This app fetches data from Polygon.io and displays it in an interactive chart.")
