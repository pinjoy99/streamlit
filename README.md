# 📈 Trading Analysis Platform

A comprehensive Streamlit-based trading analysis platform featuring multiple strategies, backtesting frameworks, and market analysis tools.

## 🚀 Features

### 📊 Trading Strategies
- **Alpaca SuperTrend Integration** - Automated trading with SuperTrend indicators
- **Trend Reversal Detection** - Advanced trend change identification
- **Options Trading Strategies** - Multi-leg options strategies
- **Rolling Piecewise Analysis** - Dynamic regression modeling

### 🔧 Backtesting Framework
- Multiple backtesting implementations (`backtest.py`, `backtest1.py`, `backtest_default.py`)
- Comprehensive performance metrics
- Daily returns analysis
- Custom strategy validation

### 📈 Market Analysis
- **Sentiment Analysis** - Market sentiment tracking
- **Piecewise Linear Modeling** - Non-linear trend analysis
- **Walmart Data Analysis** - Retail sector insights
- **Polygon API Integration** - Real-time market data

### 💹 Options Trading
- **Option App** (`optionapp.py`) - Options strategy calculator
- **Two-Options Strategies** - Multiple two-leg strategies (`twooptionsapp.py`, `twooptionsapp1.py`, `twooptionsapp2.py`)

## 📁 Repository Structure

```
streamlit/
├── 📂 .devcontainer/              # Development container config
├── 📄 alpaca_supertrend.py        # Alpaca SuperTrend strategy
├── 📄 backtest.py                 # Main backtesting framework
├── 📄 backtest1.py                # Alternative backtest
├── 📄 backtest_default.py         # Default backtest parameters
├── 📄 dailyreturns.py             # Daily returns analysis
├── 📄 optionapp.py                # Options trading app
├── 📄 pandas-datareader.py        # Data fetching utilities
├── 📄 piecewise-linear.py         # Piecewise linear modeling
├── 📄 polygonbpi.py               # Polygon API integration
├── 📄 rolling_piecewise_fit.py    # Rolling piecewise regression
├── 📄 sentiment.py                # Sentiment analysis
├── 📄 trading_log_streamlit.csv   # Trading data log
├── 📄 trend_reversal.py           # Trend reversal detection
├── 📄 trend_reversal1.py          # Enhanced trend reversal
├── 📄 twooptionsapp.py            # Two-options strategy
├── 📄 twooptionsapp1.py           # Enhanced two-options
├── 📄 twooptionsapp2.py           # Advanced two-options
├── 📄 walmart.py                  # Walmart data analysis
└── 📄 requirements.txt            # Dependencies
```

## 🛠️ Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/pinjoy99/streamlit.git
   cd streamlit
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run Streamlit apps:**
   ```bash
   # For specific strategy apps
   streamlit run alpaca_supertrend.py
   streamlit run backtest.py
   streamlit run optionapp.py
   streamlit run twooptionsapp.py

   # Or run any other .py file for specific functionality
   ```

## 🎯 Quick Start

### Backtesting
```bash
streamlit run backtest.py
```
- Upload your data or use sample datasets
- Configure strategy parameters
- Run backtest and view performance metrics

### Options Trading
```bash
streamlit run optionapp.py
```
- Enter option symbols and expiration dates
- Analyze profit/loss scenarios
- Visualize risk/reward profiles

### Trend Analysis
```bash
streamlit run trend_reversal.py
```
- Input stock symbol
- Identify trend reversals
- View technical indicators

## 📊 Key Components

### Backtesting Engine
- Multiple implementation variants for flexibility
- Customizable parameters and strategies
- Performance visualization

### Data Sources
- **Polygon API** - Real-time and historical market data
- **Yahoo Finance** - Via pandas-datareader
- **Custom datasets** - CSV trading logs

### Analysis Tools
- **SuperTrend Indicator** - Trend following strategy
- **Rolling Regression** - Dynamic market modeling
- **Sentiment Analysis** - Market psychology indicators
- **Piecewise Fitting** - Non-linear trend detection

## 🔧 Configuration

### Environment Variables
Set up API keys for external services:
```bash
# Polygon API (for market data)
export POLYGON_API_KEY=your_api_key

# Alpaca API (for trading)
export ALPACA_API_KEY=your_api_key
export ALPACA_SECRET_KEY=your_secret_key
```

## 📈 Supported Strategies

1. **SuperTrend Strategy**
   - Entry/Exit signals based on SuperTrend indicator
   - Backtestable with custom parameters

2. **Trend Reversal**
   - Identifies potential trend changes
   - Multiple implementation versions

3. **Options Strategies**
   - Covered calls, puts, spreads
   - Risk/reward visualization

4. **Piecewise Linear**
   - Market regime detection
   - Rolling window analysis

## 🎮 Usage Examples

### Running Backtest
1. Execute `backtest.py`
2. Upload trading data (CSV format)
3. Configure strategy parameters
4. Click "Run Backtest"
5. Review results in charts and tables

### Options Analysis
1. Launch `optionapp.py`
2. Enter option details:
   - Underlying symbol
   - Strike price
   - Expiration date
   - Option type (Call/Put)
3. Analyze P&L scenarios

### Market Sentiment
1. Run `sentiment.py`
2. Input market news or data
3. Get sentiment scores and analysis

## 📋 Data Format

### Trading Data CSV
Expected columns for trading data:
```csv
Date,Open,High,Low,Close,Volume
2024-01-01,100.5,102.3,99.8,101.2,1500000
```

### Options Data
- Symbol, Strike, Expiration, Type, Premium
- Greeks calculations (Delta, Gamma, Theta, Vega)

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/pinjoy99/streamlit/issues)
- **Discussions:** [GitHub Discussions](https://github.com/pinjoy99/streamlit/discussions)

## 🙏 Acknowledgments

- **Streamlit** - For the excellent web app framework
- **Polygon.io** - Market data API
- **Alpaca** - Trading platform and API
- **pandas** - Data manipulation library
- **numpy** - Numerical computing
- **yfinance** - Yahoo Finance data access

## 📊 Performance Metrics

The platform provides comprehensive performance analysis:
- Total return and CAGR
- Sharpe ratio and maximum drawdown
- Win/loss ratio
- Calmar ratio
- Monthly/Yearly performance breakdowns

---

**Built with ❤️ using Streamlit**

For more information, visit the [documentation](https://github.com/pinjoy99/streamlit/wiki) or check out the individual app files for specific usage instructions.
