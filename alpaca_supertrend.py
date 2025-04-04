import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
from datetime import datetime, timedelta
import os
import traceback
import numpy as np
from alpaca_trade_api.rest import REST, TimeFrame
from alpaca_trade_api.common import URL
import warnings

# Ignore pandas warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
warnings.simplefilter(action='ignore', category=DeprecationWarning)
pd.options.mode.chained_assignment = None # default='warn'

# --- Configuration ---
# These can be potentially overridden by Streamlit secrets if needed later
SYMBOL = "BTC/USD"
TIMEFRAME = TimeFrame.Minute
LOOKBACK_PERIODS = 100
SUPERTREND_PERIOD = 7
SUPERTREND_MULTIPLIER = 3
ORDER_SIZE_BTC = 1.0 # Consider making this a secret or input if variable
POLL_INTERVAL_SECONDS = 60 # Interval for rerun when running
LOG_FILE = 'trading_log_streamlit.csv' # Use a distinct log file name
PLOT_WINDOW_HOURS = 3

# --- Helper Functions (Adapted from main.py) ---

def connect_alpaca():
    """
    Establishes connection to the Alpaca API using Streamlit secrets.
    """
    print("Connecting to Alpaca using Streamlit secrets...")
    api_key = None
    secret_key = None
    is_paper = True # Default to paper trading

    # Use Streamlit secrets
    try:
        if "ALPACA_API_KEY" in st.secrets and "ALPACA_SECRET_KEY" in st.secrets:
            api_key = st.secrets["ALPACA_API_KEY"]
            secret_key = st.secrets["ALPACA_SECRET_KEY"]
            # Check for paper trading status in secrets, default to True if not found
            is_paper = st.secrets.get("ALPACA_PAPER", "true").lower() == "true"
            print(f"Streamlit secrets indicate paper trading: {is_paper}")
        else:
             st.error("Error: ALPACA_API_KEY or ALPACA_SECRET_KEY not found in Streamlit secrets.")
             print("Error: Required keys not found in st.secrets.")
             return None
    except Exception as e:
        st.error(f"Error accessing Streamlit secrets: {e}")
        print(f"Error accessing Streamlit secrets: {e}")
        return None

    base_url = URL("https://paper-api.alpaca.markets") if is_paper else URL("https://api.alpaca.markets")
    print(f"Using Base URL: {base_url}")

    try:
        local_api = REST(api_key, secret_key, base_url=base_url, api_version='v2')
        account = local_api.get_account()
        print(f"Connected. Account Status: {account.status}, Equity: {account.equity}, Cash: {account.cash}, Buying Power: {account.buying_power}")
        st.success(f"Connected to Alpaca ({'Paper' if is_paper else 'Live'}). Status: {account.status}")
        return local_api # Return the api object on success
    except Exception as e:
        st.error(f"Error connecting to Alpaca: {e}")
        print(f"Error connecting to Alpaca: {e}")
        return None # Return None on failure

def get_current_position_details(api):
    """Gets the current position quantity and unrealized PnL."""
    if api is None: return None, None
    position_symbol = SYMBOL.replace('/', '')
    qty = 0.0; unrealized_pl = 0.0
    try:
        position = api.get_position(position_symbol)
        qty = float(position.qty)
        unrealized_pl = float(position.unrealized_pl)
        if position.side != 'long': qty = 0.0; unrealized_pl = 0.0
        return qty, unrealized_pl
    except Exception as e:
        error_str = str(e).lower()
        if "position does not exist" in error_str or "404 client error" in error_str or "not found" in error_str:
             return 0.0, 0.0
        else:
            print(f"Error getting position details for {position_symbol}: {e}")
            st.warning(f"Error getting position details: {e}")
            return None, None

def get_account_details(api):
    """Gets current account equity, cash, and buying power."""
    if api is None: return None, None, None
    try:
        account = api.get_account()
        equity = float(account.equity)
        cash = float(account.cash)
        buying_power = float(account.buying_power)
        return equity, cash, buying_power
    except Exception as e:
        print(f"Error getting account details: {e}")
        st.error(f"Error getting account details: {e}")
        return None, None, None

def get_data(api):
    """Fetches historical data for the symbol."""
    if api is None: return None
    try:
        now = datetime.utcnow()
        start_dt = now - timedelta(minutes=LOOKBACK_PERIODS * 2 + 10)
        end_dt = now - timedelta(minutes=1)
        start_iso = start_dt.isoformat() + "Z"; end_iso = end_dt.isoformat() + "Z"
        bars = api.get_crypto_bars(SYMBOL, TIMEFRAME, start=start_iso, end=end_iso).df
        if bars.empty: return None
        if 'exchange' in bars.columns:
            bars_filtered = bars[bars.exchange == 'CBSE']
            if not bars_filtered.empty: bars = bars_filtered
        if bars.empty: return None
        bars.columns = map(str.lower, bars.columns)
        rename_map = {'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'}
        bars.rename(columns=rename_map, inplace=True)
        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        if not all(col in bars.columns for col in required_cols): return None
        bars.index = pd.to_datetime(bars.index); bars.sort_index(inplace=True)
        if len(bars) < LOOKBACK_PERIODS: return None
        return bars
    except Exception as e:
        print(f"Error fetching/processing data: {e}"); st.error(f"Error fetching/processing data: {e}")
        return None

def tr(data):
    if not all(col in data.columns for col in ['High', 'Low', 'Close']): return None
    data = data.copy(); data['previous_close'] = data['Close'].shift(1)
    data['high-low'] = abs(data['High'] - data['Low'])
    data['high-pc'] = abs(data['High'] - data['previous_close'])
    data['low-pc'] = abs(data['Low'] - data['previous_close'])
    return data[['high-low', 'high-pc', 'low-pc']].max(axis=1)

def atr(data, period):
    data = data.copy(); data['tr'] = tr(data)
    if data['tr'] is None: return None
    data.dropna(subset=['tr'], inplace=True)
    if data.empty or len(data) < period: return None
    return data['tr'].rolling(period).mean()

def supertrend(df, period=SUPERTREND_PERIOD, atr_multiplier=SUPERTREND_MULTIPLIER):
    if df is None or df.empty: return None
    if not all(col in df.columns for col in ['High', 'Low', 'Close']): return None
    df = df.copy(); df['atr'] = atr(df, period)
    if df['atr'] is None: return None
    df.dropna(subset=['atr'], inplace=True)
    if df.empty: return None
    hl2 = (df['High'] + df['Low']) / 2
    df['upperband'] = hl2 + (atr_multiplier * df['atr'])
    df['lowerband'] = hl2 - (atr_multiplier * df['atr'])
    df['in_uptrend'] = True
    for current in range(1, len(df.index)):
        previous = current - 1; idx_current = df.index[current]; idx_previous = df.index[previous]
        close_current = df.loc[idx_current, 'Close']; upperband_prev = df.loc[idx_previous, 'upperband']
        lowerband_prev = df.loc[idx_previous, 'lowerband']; lowerband_current = df.loc[idx_current, 'lowerband']
        upperband_current = df.loc[idx_current, 'upperband']; in_uptrend_prev = df.loc[idx_previous, 'in_uptrend']
        if close_current > upperband_prev: df.loc[idx_current, 'in_uptrend'] = True
        elif close_current < lowerband_prev: df.loc[idx_current, 'in_uptrend'] = False
        else:
            df.loc[idx_current, 'in_uptrend'] = in_uptrend_prev
            if df.loc[idx_current, 'in_uptrend'] and lowerband_current < lowerband_prev: df.loc[idx_current, 'lowerband'] = lowerband_prev
            if not df.loc[idx_current, 'in_uptrend'] and upperband_current > upperband_prev: df.loc[idx_current, 'upperband'] = upperband_prev
    return df

def check_signals_and_trade(api, df, current_qty):
    if api is None: return "Hold (Error)"
    print("Checking for buy/sell signals...")
    if df is None or len(df) < 2: return "Hold"
    last_row = df.iloc[-1]; prev_row = df.iloc[-2]
    signal_action = "Hold"; order_symbol = SYMBOL.replace('/', '')
    print(f"Supertrend - Previous: {'Uptrend' if prev_row['in_uptrend'] else 'Downtrend'}, Current: {'Uptrend' if last_row['in_uptrend'] else 'Downtrend'}")
    print(f"Current Position: {current_qty} {order_symbol}")
    is_long = current_qty > 1e-9; is_flat = not is_long
    trend_flipped_up = (not prev_row['in_uptrend'] and last_row['in_uptrend'])
    trend_flipped_down = (prev_row['in_uptrend'] and not last_row['in_uptrend'])
    print(f"Debug Check: FlippedUp={trend_flipped_up}, FlippedDown={trend_flipped_down}, IsLong={is_long}, IsFlat={is_flat}")
    try:
        if trend_flipped_up:
            print("Signal: Uptrend detected.")
            if is_flat:
                print(f"Action: Buying {ORDER_SIZE_BTC} {order_symbol}")
                api.submit_order(symbol=order_symbol, qty=ORDER_SIZE_BTC, side='buy', type='market', time_in_force='gtc')
                signal_action = "Buy"
            else: print("Action: Already Long, Holding."); signal_action = "Hold"
        elif trend_flipped_down:
            print("Signal: Downtrend detected.")
            if is_long:
                close_qty = abs(current_qty)
                print(f"Action: Selling {close_qty} {order_symbol} to close position.")
                api.submit_order(symbol=order_symbol, qty=close_qty, side='sell', type='market', time_in_force='gtc')
                signal_action = "Sell"
            else: print("Action: Already Flat, Holding."); signal_action = "Hold"
        else: print("Signal: No trend change detected. Holding."); signal_action = "Hold"
    except Exception as e: print(f"Error submitting order: {e}"); signal_action = "Hold (Error)"
    return signal_action

def log_data(timestamp, price, trend_status, upper_band, lower_band, holding_qty, market_value, cash, equity, transaction, cumulative_pnl, minutely_pnl, unrealized_pnl, cumulative_realized_pnl, net_liquidation_value):
    log_entry = {'Timestamp': timestamp, 'Price': price, 'Trend': trend_status, 'UpperBand': upper_band, 'LowerBand': lower_band, 'HoldingQty': holding_qty, 'MarketValue': market_value, 'Cash': cash, 'Equity': equity, 'Transaction': transaction, 'CumulativePnL': cumulative_pnl, 'MinutelyPnL': minutely_pnl, 'UnrealizedPnL': unrealized_pnl, 'CumulativeRealizedPnL': cumulative_realized_pnl, 'NetLiquidationValue': net_liquidation_value}
    new_row = pd.DataFrame([log_entry])
    try:
        file_exists = os.path.exists(LOG_FILE)
        header_order = ['Timestamp', 'Price', 'Trend', 'UpperBand', 'LowerBand', 'HoldingQty', 'MarketValue', 'Cash', 'Equity', 'Transaction', 'CumulativePnL', 'MinutelyPnL', 'UnrealizedPnL', 'CumulativeRealizedPnL', 'NetLiquidationValue']
        new_row.to_csv(LOG_FILE, mode='a', header=not file_exists, index=False, columns=header_order)
    except Exception as e: print(f"Error logging data: {e}")

def run_bot_cycle(api, current_run_state):
    local_initial_equity = current_run_state.get('initial_equity')
    local_previous_minute_equity = current_run_state.get('previous_minute_equity')
    local_cumulative_realized_pnl = current_run_state.get('cumulative_realized_pnl', 0.0)
    local_previous_minute_unrealized_pnl = current_run_state.get('previous_minute_unrealized_pnl', 0.0)
    print("-" * 30); print(f"Running cycle at {datetime.now().isoformat()}")
    if api is None: print("API object is None..."); return current_run_state
    df_raw = get_data(api)
    if df_raw is None or df_raw.empty: print("Failed to get data..."); return current_run_state
    df_supertrend = supertrend(df_raw)
    if df_supertrend is None or df_supertrend.empty: print("Failed to calculate Supertrend..."); return current_run_state
    last_row = df_supertrend.iloc[-1]; current_price = last_row['Close']; current_time = datetime.now()
    api_equity, api_cash, api_buying_power = get_account_details(api)
    current_position_qty, api_unrealized_pnl = get_current_position_details(api)
    if api_equity is None or api_cash is None or current_position_qty is None or api_unrealized_pnl is None:
        print("Failed to get account/position details..."); return current_run_state
    market_value = current_position_qty * current_price; calculated_equity = api_cash + market_value
    if local_initial_equity is None:
        local_initial_equity = calculated_equity; print(f"Initial equity set (calculated): {local_initial_equity}")
        local_previous_minute_equity = calculated_equity; local_previous_minute_unrealized_pnl = api_unrealized_pnl
    cumulative_pnl = calculated_equity - local_initial_equity
    minutely_pnl = calculated_equity - local_previous_minute_equity if local_previous_minute_equity is not None else 0
    minutely_realized_pnl = 0.0
    if local_previous_minute_equity is not None:
        change_in_calculated_equity = calculated_equity - local_previous_minute_equity
        change_in_api_unrealized_pnl = api_unrealized_pnl - local_previous_minute_unrealized_pnl
        minutely_realized_pnl = change_in_calculated_equity - change_in_api_unrealized_pnl
        local_cumulative_realized_pnl += minutely_realized_pnl
    transaction_type = check_signals_and_trade(api, df_supertrend, current_position_qty)
    print(f"Debug API State: API Equity={api_equity}, API Cash={api_cash}, API Unrealized PnL={api_unrealized_pnl}")
    print(f"Debug Calculated: Market Value={market_value}, Calculated Equity={calculated_equity}")
    print(f"Debug PnL: Prev Calc Equity={local_previous_minute_equity}, Minutely Total PnL (Calc)={minutely_pnl}")
    print(f"Debug Realized PnL: Minutely={minutely_realized_pnl}, Cumulative={local_cumulative_realized_pnl}")
    log_data(timestamp=current_time, price=current_price, trend_status='Uptrend' if last_row['in_uptrend'] else 'Downtrend', upper_band=last_row['upperband'], lower_band=last_row['lowerband'], holding_qty=current_position_qty, market_value=market_value, cash=api_cash, equity=calculated_equity, transaction=transaction_type, cumulative_pnl=cumulative_pnl, minutely_pnl=minutely_pnl, unrealized_pnl=api_unrealized_pnl, cumulative_realized_pnl=local_cumulative_realized_pnl, net_liquidation_value=calculated_equity)
    updated_run_state = {'initial_equity': local_initial_equity, 'previous_minute_equity': calculated_equity, 'cumulative_realized_pnl': local_cumulative_realized_pnl, 'previous_minute_unrealized_pnl': api_unrealized_pnl, 'equity': api_equity, 'cash': api_cash, 'buying_power': api_buying_power, 'position_qty': current_position_qty, 'unrealized_pnl': api_unrealized_pnl, 'market_value': market_value, 'account_status': api.get_account().status}
    print(f"Cycle complete at {datetime.now().isoformat()}"); print("-" * 30)
    return updated_run_state

def close_position_on_exit(api):
    print("\nAttempting to close open position before exiting...")
    if api is None: print("API not connected."); return
    current_qty, _ = get_current_position_details(api)
    order_symbol = SYMBOL.replace('/', '')
    if current_qty is not None and current_qty > 1e-9:
        side_to_close = 'sell'; qty_to_close = abs(current_qty)
        print(f"Current position: {current_qty}. Submitting market {side_to_close} order for {qty_to_close} {order_symbol}...")
        try:
            api.submit_order(symbol=order_symbol, qty=qty_to_close, side=side_to_close, type='market', time_in_force='gtc')
            print("Position closing order submitted."); time.sleep(5)
        except Exception as e: print(f"Error submitting closing order: {e}")
    elif current_qty == 0.0: print("No open position to close.")
    else: print(f"Could not determine position or position is not long ({current_qty}). No close action taken.")
    print("Position closing attempt finished.")

# --- Streamlit App Configuration ---
st.set_page_config(layout="wide", page_title="Alpaca Supertrend Bot")

# --- Initialize Session State ---
default_state = {
    'running': False, 'api_connected': False, 'status_message': "Idle", 'last_run_time': None,
    'initial_equity': None, 'previous_minute_equity': None, 'cumulative_realized_pnl': 0.0,
    'previous_minute_unrealized_pnl': 0.0, 'equity': 0.0, 'cash': 0.0, 'buying_power': 0.0,
    'position_qty': 0.0, 'unrealized_pnl': 0.0, 'market_value': 0.0,
    'account_status': "Disconnected", 'api_object': None
}
for key, value in default_state.items():
    if key not in st.session_state: st.session_state[key] = value

# --- UI Layout ---
st.title("Alpaca Supertrend BTC Trading Bot (Streamlit Cloud Ready)")

# Sidebar for controls
with st.sidebar:
    st.header("Controls")
    # Check if secrets are loaded before enabling connect button
    secrets_loaded = "ALPACA_API_KEY" in st.secrets and "ALPACA_SECRET_KEY" in st.secrets
    if not secrets_loaded:
        st.warning("API keys not found in Streamlit Secrets. Please configure them in your app settings.")
    connect_button = st.button("Connect to Alpaca", disabled=st.session_state['api_connected'] or not secrets_loaded)
    start_button = st.button("Start Bot", disabled=not st.session_state['api_connected'] or st.session_state['running'])
    stop_button = st.button("Stop Bot", disabled=not st.session_state['running'])

    st.header("Configuration")
    st.text_input("Symbol", value=SYMBOL, disabled=True)
    st.number_input("Order Size (BTC)", value=ORDER_SIZE_BTC, disabled=True)
    st.number_input("Poll Interval (s)", value=POLL_INTERVAL_SECONDS, disabled=True)
    st.number_input("Plot Window (hr)", value=PLOT_WINDOW_HOURS, disabled=True)

# Main area for status and charts
status_placeholder = st.empty()
col1, col2, col3, col4 = st.columns(4)
equity_placeholder = col1.empty()
cash_placeholder = col2.empty()
market_value_placeholder = col3.empty()
position_placeholder = col4.empty()
col5, col6, col7 = st.columns(3)
cum_realized_pnl_placeholder = col5.empty()
unrealized_pnl_placeholder = col6.empty()
total_pnl_placeholder = col7.empty()
chart_placeholder = st.empty()
log_placeholder = st.empty()

# --- Control Logic ---
if connect_button:
    with st.spinner("Connecting..."):
        api_obj = connect_alpaca() # Uses st.secrets
        if api_obj:
            st.session_state['api_object'] = api_obj
            st.session_state['api_connected'] = True
            try:
                equity, cash, buying_power = get_account_details(st.session_state['api_object'])
                qty, unrealized_pl = get_current_position_details(st.session_state['api_object'])
                account_status = st.session_state['api_object'].get_account().status
                if equity is not None:
                    st.session_state['equity'] = equity; st.session_state['cash'] = cash
                    st.session_state['buying_power'] = buying_power; st.session_state['position_qty'] = qty
                    st.session_state['unrealized_pnl'] = unrealized_pl; st.session_state['market_value'] = 0 # Placeholder
                    st.session_state['account_status'] = account_status
                    st.session_state['status_message'] = "Connected. Fetched initial state."
                else: raise Exception("Failed to fetch account details after connection.")
            except Exception as e:
                st.session_state['status_message'] = f"Connected, but failed to fetch initial state: {e}"
                st.session_state['api_connected'] = False; st.session_state['api_object'] = None
        else:
            st.session_state['status_message'] = "Connection Failed."
            st.session_state['api_connected'] = False; st.session_state['api_object'] = None
    st.rerun()

if start_button:
    st.session_state['running'] = True
    st.session_state['status_message'] = "Bot Started. Running first cycle..."
    st.session_state['last_run_time'] = datetime.now()
    st.rerun()

if stop_button:
    st.session_state['running'] = False
    st.session_state['status_message'] = "Bot Stopped."
    # Optional: Add close_position_on_exit call here if desired for Streamlit stop button
    # with st.spinner("Attempting to close position..."):
    #     close_position_on_exit(st.session_state.get('api_object'))
    #     st.info("Close position attempt finished.")
    st.rerun()

# --- Main Bot Loop (runs if state is 'running') ---
if st.session_state['running'] and st.session_state['api_connected']:
    try:
        current_run_state = {
            'initial_equity': st.session_state.initial_equity,
            'previous_minute_equity': st.session_state.previous_minute_equity,
            'cumulative_realized_pnl': st.session_state.cumulative_realized_pnl,
            'previous_minute_unrealized_pnl': st.session_state.previous_minute_unrealized_pnl,
            # Pass other state if needed by run_bot_cycle
        }
        updated_state = run_bot_cycle(st.session_state['api_object'], current_run_state)
        for key, value in updated_state.items(): st.session_state[key] = value
        st.session_state['last_run_time'] = datetime.now()
    except Exception as e:
        st.session_state['status_message'] = f"Error during cycle: {e}"
        st.error(traceback.format_exc()); st.session_state['running'] = False

# --- Update UI Elements ---
status_text = f"{st.session_state.status_message}"
if st.session_state.last_run_time: status_text += f" (Last run: {st.session_state.last_run_time.strftime('%Y-%m-%d %H:%M:%S')})"
status_placeholder.info(status_text)
st.sidebar.metric("Account Status", st.session_state.account_status)

if st.session_state['api_connected']:
    equity_placeholder.metric("Equity", f"${st.session_state.equity:,.2f}")
    cash_placeholder.metric("Cash", f"${st.session_state.cash:,.2f}")
    market_value_placeholder.metric("Market Value", f"${st.session_state.market_value:,.2f}")
    position_placeholder.metric("Position (BTC)", f"{st.session_state.position_qty:,.4f}")
    cum_realized_pnl_placeholder.metric("Cumulative Realized PnL", f"${st.session_state.cumulative_realized_pnl:,.2f}")
    unrealized_pnl_placeholder.metric("Unrealized PnL", f"${st.session_state.unrealized_pnl:,.2f}")
    total_pnl = st.session_state.cumulative_realized_pnl + st.session_state.unrealized_pnl
    total_pnl_placeholder.metric("Total PnL", f"${total_pnl:,.2f}")

# --- Charting (using Plotly, reading from CSV) ---
def load_and_prepare_log_data(log_file_path, window_hours):
    if not os.path.exists(log_file_path): return pd.DataFrame()
    try:
        log_df = pd.read_csv(log_file_path); log_df['Timestamp'] = pd.to_datetime(log_df['Timestamp'])
        log_df.sort_values('Timestamp', inplace=True)
        if not log_df.empty:
            latest_time = log_df['Timestamp'].iloc[-1]
            start_time_window = latest_time - timedelta(hours=window_hours)
            log_df = log_df[log_df['Timestamp'] >= start_time_window]
        return log_df
    except Exception as e: st.error(f"Error loading/preparing log data: {e}"); return pd.DataFrame()

log_df_display = load_and_prepare_log_data(LOG_FILE, PLOT_WINDOW_HOURS)

if not log_df_display.empty:
    fig_chart = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.05, subplot_titles=("Price & Signals", "Equity", "Cumulative PnL"))
    fig_chart.add_trace(go.Scatter(x=log_df_display['Timestamp'], y=log_df_display['Price'], mode='lines', name='Price', line=dict(color='blue')), row=1, col=1)
    fig_chart.add_trace(go.Scatter(x=log_df_display['Timestamp'], y=log_df_display['UpperBand'], mode='lines', name='Upper Band', line=dict(color='red', dash='dash'), opacity=0.7), row=1, col=1)
    fig_chart.add_trace(go.Scatter(x=log_df_display['Timestamp'], y=log_df_display['LowerBand'], mode='lines', name='Lower Band', line=dict(color='green', dash='dash'), opacity=0.7), row=1, col=1)
    buy_signals = log_df_display[log_df_display['Transaction'] == 'Buy']; sell_signals = log_df_display[log_df_display['Transaction'] == 'Sell']
    fig_chart.add_trace(go.Scatter(x=buy_signals['Timestamp'], y=buy_signals['Price'], mode='markers', name='Buy', marker=dict(symbol='triangle-up', color='lime', size=10, line=dict(width=1, color='black'))), row=1, col=1)
    fig_chart.add_trace(go.Scatter(x=sell_signals['Timestamp'], y=sell_signals['Price'], mode='markers', name='Sell', marker=dict(symbol='triangle-down', color='red', size=10, line=dict(width=1, color='black'))), row=1, col=1)
    fig_chart.add_trace(go.Scatter(x=log_df_display['Timestamp'], y=log_df_display['Equity'], mode='lines', name='Equity', line=dict(color='purple')), row=2, col=1)
    fig_chart.add_trace(go.Scatter(x=log_df_display['Timestamp'], y=log_df_display['CumulativeRealizedPnL'], mode='lines', name='Cum. Realized PnL', line=dict(color='orange')), row=3, col=1)
    fig_chart.update_layout(height=700, title_text="Bot Performance Monitor", showlegend=True, legend=dict(traceorder='normal'))
    fig_chart.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])])
    fig_chart.update_yaxes(title_text="Price ($)", row=1, col=1); fig_chart.update_yaxes(title_text="Equity ($)", row=2, col=1); fig_chart.update_yaxes(title_text="PnL ($)", row=3, col=1)
    chart_placeholder.plotly_chart(fig_chart, use_container_width=True)
else: chart_placeholder.info("Waiting for log data to generate chart...")

# --- Log Display (Reading from CSV) ---
if os.path.exists(LOG_FILE):
    try:
        log_tail_df = pd.read_csv(LOG_FILE).tail(20) # Show more lines
        log_placeholder.dataframe(log_tail_df)
    except Exception as e: log_placeholder.error(f"Error reading log file: {e}")
else: log_placeholder.info("Log file not found yet.")

# --- Auto-refresh Logic ---
if st.session_state['running']:
    time.sleep(POLL_INTERVAL_SECONDS)
    st.rerun()
