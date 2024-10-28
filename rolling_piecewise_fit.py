import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from piecewise_regression import Fit
from scipy.stats import norm

# Function to fetch SPX data
def get_spx_data():
    spx = yf.Ticker("^GSPC")
    data = spx.history(start="2023-01-01", end="2023-12-31")
    return data['Close']

# Function to perform piecewise regression on a window
def piecewise_regression(x, y, n_breakpoints=2):
    try:
        model = Fit(x, y, n_breakpoints=n_breakpoints)
        results = model.get_results()
        breakpoints = results['estimates']['breakpoints']
        slopes = results['estimates']['slopes']
        return breakpoints, slopes
    except:
        return [], []

# Function to analyze rolling windows
def analyze_rolling_windows(data, window_size, n_breakpoints):
    all_slope_changes = []
    breakpoints_with_significant_changes = []

    for i in range(len(data) - window_size + 1):
        window = data.iloc[i:i+window_size]
        x = np.arange(len(window))
        y = window.values
        
        breakpoints, slopes = piecewise_regression(x, y, n_breakpoints)
        
        if len(slopes) > 1:
            slope_changes = np.diff(slopes)
            all_slope_changes.extend(slope_changes)
            
            for j, change in enumerate(slope_changes):
                if abs(change) > np.std(all_slope_changes):
                    breakpoints_with_significant_changes.append(window.index[int(breakpoints[j])])

    return all_slope_changes, breakpoints_with_significant_changes

# Streamlit app
st.title("S&P 500 Piecewise Regression Analysis")

# Sidebar
window_size = st.sidebar.number_input("Rolling Window Size", min_value=30, max_value=252, value=60)
n_breakpoints = st.sidebar.number_input("Number of Breakpoints", min_value=1, max_value=5, value=2)

# Fetch data
spx_data = get_spx_data()

# Analyze rolling windows
slope_changes, significant_breakpoints = analyze_rolling_windows(spx_data, window_size, n_breakpoints)

# Plot SPX time series with breakpoints
fig, ax = plt.subplots(figsize=(12, 6))
ax.plot(spx_data.index, spx_data.values)
ax.set_title("S&P 500 (2023) with Significant Breakpoints")
ax.set_xlabel("Date")
ax.set_ylabel("Price")

for bp in significant_breakpoints:
    ax.axvline(bp, color='r', linestyle='--', alpha=0.5)

st.pyplot(fig)

# Histogram of slope changes
fig, ax = plt.subplots(figsize=(10, 5))
ax.hist(slope_changes, bins=30, edgecolor='black')
ax.set_title("Histogram of Slope Changes")
ax.set_xlabel("Slope Change")
ax.set_ylabel("Frequency")
st.pyplot(fig)

# Summary statistics
st.subheader("Summary Statistics")
st.write(f"Total number of windows analyzed: {len(spx_data) - window_size + 1}")
st.write(f"Number of significant breakpoints detected: {len(significant_breakpoints)}")
st.write(f"Mean slope change: {np.mean(slope_changes):.4f}")
st.write(f"Standard deviation of slope changes: {np.std(slope_changes):.4f}")
