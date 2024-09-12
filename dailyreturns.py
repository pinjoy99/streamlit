import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.title('SPX Daily Returns Analysis')

# Download data
@st.cache_data
def get_data():
    end_date = datetime.now()
    start_date = end_date - timedelta(days=3650)  # 10 years
    ticker = 'SPX'
    data = yf.download(ticker, start=start_date, end=end_date)
    data['Returns'] = data['Adj Close'].pct_change()
    return data

data = get_data()

# Display OHLC data
st.subheader('OHLC Data')
st.dataframe(data)

# Histogram of daily returns
st.subheader('Histogram of Daily Simple Returns')
fig, ax = plt.subplots(figsize=(10, 6))
sns.histplot(data['Returns'].dropna(), bins=50, kde=True, ax=ax)
ax.set_title('Distribution of Daily Simple Returns for SPX')
ax.set_xlabel('Daily Returns')
ax.set_ylabel('Frequency')
ax.grid(True)
st.pyplot(fig)

# Interactive histogram using Plotly
st.subheader('Interactive Histogram of Daily Simple Returns')
fig = go.Figure(data=[go.Histogram(x=data['Returns'].dropna(), nbinsx=50)])
fig.update_layout(title='Distribution of Daily Simple Returns for SPX',
                  xaxis_title='Daily Returns',
                  yaxis_title='Frequency')
st.plotly_chart(fig)

# Count days below thresholds
st.subheader('Days with Returns Below Thresholds')
thresholds = [-0.05, -0.04, -0.03, -0.02, -0.01]
days_below = {f"Below {threshold*100}%": (data['Returns'] < threshold).sum() for threshold in thresholds}
st.table(pd.DataFrame.from_dict(days_below, orient='index', columns=['Count']))

# Find dates and returns below -2%
st.subheader('Dates and Returns Below -2%')
below_2_percent = data[data['Returns'] < -0.02][['Returns']].dropna()
st.dataframe(below_2_percent)

# Interactive scatter plot for returns below -2%
st.subheader('Interactive Chart: Returns Below -2%')
fig = go.Figure(data=go.Scatter(x=below_2_percent.index, y=below_2_percent['Returns'],
                                mode='markers',
                                marker=dict(color=below_2_percent['Returns'], 
                                            colorscale='Viridis',
                                            showscale=True)))
fig.update_layout(title='Daily Returns Below -2%',
                  xaxis_title='Date',
                  yaxis_title='Return')
st.plotly_chart(fig)
