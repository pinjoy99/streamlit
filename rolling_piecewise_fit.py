import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import pwlf
import plotly.graph_objects as go
import plotly.figure_factory as ff

# Function to perform piecewise linear regression
def perform_pwlf(x, y, num_segments):
    model = pwlf.PiecewiseLinFit(x, y)
    model.fit(num_segments)
    return model.fit_breaks, model.slopes

# Function to calculate slope changes
def calculate_slope_changes(slopes):
    return np.diff(slopes)

# Streamlit app
st.title("SPX Piecewise Linear Regression Analysis")

# Sidebar for user input
window_size = st.sidebar.number_input("Rolling Window Size (days)", min_value=5, max_value=21, value=9)
num_segments = st.sidebar.number_input("Number of Segments", min_value=2, max_value=10, value=3)

# Fetch SPX data
spx_data = yf.download("^GSPC", start="2023-01-01", end="2023-12-31")
spx_data.reset_index(inplace=True)

# Prepare data for analysis
x = (spx_data['Date'] - spx_data['Date'].min()).dt.days.values
y = spx_data['Close'].values

# Perform rolling window analysis
results = []
all_breakpoints = []
all_slope_changes = []

for i in range(len(spx_data) - window_size + 1):
    window_x = x[i:i+window_size]
    window_y = y[i:i+window_size]
    
    breaks, slopes = perform_pwlf(window_x, window_y, num_segments)
    slope_changes = calculate_slope_changes(slopes)
    
    results.append({
        'Window Start': spx_data['Date'].iloc[i],
        'Window End': spx_data['Date'].iloc[i+window_size-1],
        'Breakpoints': breaks[1:-1],
        'Slopes': slopes
    })
    
    all_breakpoints.extend(breaks[1:-1])
    all_slope_changes.extend(slope_changes)

# Create summary table
summary_df = pd.DataFrame(results)
st.subheader("Summary Table")
st.dataframe(summary_df)

# Create histogram of slope changes
st.subheader("Histogram of Slope Changes")
fig = ff.create_distplot([all_slope_changes], ['Slope Changes'], bin_size=0.01)
st.plotly_chart(fig)

# Plot SPX time-series with breakpoints
st.subheader("SPX Time-series with Breakpoints")
fig = go.Figure()

fig.add_trace(go.Scatter(x=spx_data['Date'], y=spx_data['Close'], mode='lines', name='SPX'))

for bp in all_breakpoints:
    bp_date = spx_data['Date'].min() + pd.Timedelta(days=int(bp))
    fig.add_vline(x=bp_date, line_dash="dash", line_color="red", opacity=0.3)

fig.update_layout(xaxis_title="Date", yaxis_title="SPX Close Price")
st.plotly_chart(fig)

st.write("Note: Red dashed lines represent breakpoints from all rolling windows.")
