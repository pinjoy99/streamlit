import streamlit as st
import yfinance as yf
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import pwlf

# Define function for piecewise linear fitting
def piecewise_linear(x, x0, y0, k1, k2):
    return np.piecewise(x, [x < x0], 
                        [lambda x: k1*x + y0-k1*x0, 
                         lambda x: k2*(x-x0) + y0])

# Get top 10 most traded stocks and ETFs (example symbols)
symbols = ['AAPL', 'MSFT', 'SPY', 'QQQ', 'TSLA', 'AMZN', 'GOOGL', 'FB', 'NVDA', 'NFLX']

st.sidebar.title("Stock/ETF Selector")
selected_symbol = st.sidebar.selectbox("Select a Stock/ETF", symbols)

period = st.sidebar.number_input("Select period (days)", min_value=1, value=7)

# Download data
#data = yf.download(selected_symbol, period=f'{period}d')
data = yf.download(selected_symbol, period='1mo')

st.title(f"{selected_symbol} Price Analysis")

if not data.empty:
    st.line_chart(data['Close'])

    # Perform piecewise linear fitting
    x = np.arange(len(data))
    y = data['Close'].values

    # Fit the model
    pwlf_model = pwlf.PiecewiseLinFit(x, y)
    breaks = pwlf_model.fit(2)
    y_hat = pwlf_model.predict(x)

    # Plotting
    fig, ax = plt.subplots()
    ax.plot(x, y, 'bo', label='Data')
    ax.plot(x, y_hat, 'r-', label='Fitted Piecewise')
    ax.set_xlabel('Days')
    ax.set_ylabel('Price')
    ax.set_title('Piecewise Linear Fit')
    ax.legend()

    st.pyplot(fig)

    # Display fitting results
    slopes = pwlf_model.slopes
    intercepts = pwlf_model.intercepts

    st.write(f"Slopes: {slopes}")
    st.write(f"Intercepts: {intercepts}")
    st.write(f"Breakpoints: {breaks}")

else:
    st.write("No data available for the selected period.")
