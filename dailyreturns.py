import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.title('SPX Daily OHLC Analysis')

# Download SPX data for the past 10 years
end_date = datetime.now()
start_date = end_date - timedelta(days=3650)
ticker = "^GSPC"  # SPX ticker symbol

@st.cache_data
def load_data():
    data = yf.download(ticker, start=start_date, end=end_date)
    data['Daily_Return'] = data['Close'].pct_change()
    return data

data = load_data()

# Display OHLC data
st.subheader('SPX OHLC Data')
st.dataframe(data)

# Calculate and display histogram of daily returns
st.subheader('Histogram of Daily Returns')
fig_hist = px.histogram(data, x='Daily_Return', nbins=200, 
                        title='Distribution of Daily Returns')
st.plotly_chart(fig_hist, use_container_width=True)

# Calculate and display return thresholds
st.subheader('Return Thresholds')
thresholds = [-0.05, -0.04, -0.03, -0.02, -0.01]
threshold_counts = [(data['Daily_Return'] < threshold).sum() for threshold in thresholds]
threshold_df = pd.DataFrame({
    'Threshold': [f"{threshold:.1%}" for threshold in thresholds],
    'Number of Days': threshold_counts
})
st.table(threshold_df)

# Plot daily returns with marked points below -2%
st.subheader('Daily Returns Over Time')
fig_returns = go.Figure()
fig_returns.add_trace(go.Scatter(x=data.index, y=data['Daily_Return'], 
                                 mode='lines', name='Daily Returns'))

# Mark points below -2%
below_threshold = data[data['Daily_Return'] < -0.02]
fig_returns.add_trace(go.Scatter(x=below_threshold.index, y=below_threshold['Daily_Return'], 
                                 mode='markers', name='Below -2%', 
                                 marker=dict(color='red', size=8)))

fig_returns.update_layout(title='Daily Returns with Points Below -2% Marked',
                          xaxis_title='Date',
                          yaxis_title='Daily Return')

st.plotly_chart(fig_returns, use_container_width=True)
