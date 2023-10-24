import json
import os
import time
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
# Custom Libraries
import mt5_lib
import strategies.ema_cross_strategy as ema
from plotly.subplots import make_subplots

# Location of settings.json
settings_filepath = "settings.json"  # <- This can be modified to be your own settings filepath
trade_data = {}
# Function to import settings from settings.json
def get_project_settings(import_filepath):
    """
    Function to import settings from settings.json
    :param import_filepath: path to settings.json
    :return: settings as a dictionary object
    """
    # Test the filepath to make sure it exists
    if os.path.exists(import_filepath):
        # If yes, import the file
        with open(import_filepath, "r") as f:
            # Read the information
            project_settings = json.load(f)
        # Return the project settings
        return project_settings
    # Notify user if settings.json doesn't exist
    else:
        raise ImportError("settings.json does not exist at provided location")


# Function to repeat startup procedures
def start_up(project_settings):
    """
    Function to manage start up procedures for App. Includes starting/testing exchanges
    initializing symbols and anything else to ensure app start is successful.
    :param project_settings: json object of the project settings
    :return: Boolean. True if app start up is successful. False if not.
    """
    # Start MetaTrader 5
    startup = mt5_lib.start_mt5(project_settings=project_settings)
    # If startup successful, let user know
    if startup:
        st.write("MetaTrader startup successful")
        # Initialize symbols
        # Extract symbols from project settings
        symbols = project_settings["mt5"]["symbols"]
        # Iterate through the symbols to enable
        for symbol in symbols:
            outcome = mt5_lib.initialize_symbol(symbol)
            # Update the user
            if outcome is True:
                st.write(f"Symbol {symbol} initialized")
            else:
                raise Exception(f"{symbol} not initialized")
        return True
    # Default return is False
    return False


# Function to run the strategy
def run_strategy(project_settings):
    global trade_data
    # Extract the symbols to be traded
    symbols = project_settings["mt5"]["symbols"]
    # Extract the timeframe to be traded
    timeframe = project_settings["mt5"]["timeframe"]
    # Strategy Risk Management
    # Get a list of open orders
    orders = mt5_lib.get_all_open_orders()
    # Iterate through the open orders and cancel
    for order in orders:
        mt5_lib.cancel_order(order)
    # Run through the strategy of the specified symbols
    for symbol in symbols:
        # Strategy Risk Management
        # Generate the comment string
        comment_string = f"EMA_Cross_strategy_{symbol}"
        # Cancel any open orders related to the symbol and strategy
        mt5_lib.cancel_filtered_orders(
            symbol=symbol,
            comment=comment_string
        )
        # Trade Strategy
        trade_data = ema.ema_cross_strategy(
            symbol=symbol,
            timeframe=timeframe,
            ema_one=200,
            ema_two=50,
            balance=10000,
            amount_to_risk=0.01
        )
        if trade_data:
            st.write(f"Trade Made on {symbol}")
        else:
            st.write(f"No trade for {symbol}")
    # Return True. Previous code will throw a breaking error if anything goes wrong.
    return True, trade_data


def display_trade_data(trade_data):
    print(trade_data)
    # Convert the trade data to a dictionary
    fig = make_subplots(rows=len(trade_data), cols=1, shared_xaxes=True, vertical_spacing=0.05)
    for i, (symbol, trade_data_item) in enumerate(trade_data.items()):
        data_dict = trade_data_item[1]  # Extract the dictionary from the tuple
        candlestick = go.Candlestick(
            x=data_dict['time'],
            open=data_dict['open'],
            high=data_dict['high'],
            low=data_dict['low'],
            close=data_dict['close'],
            name=symbol
        )
        fig.add_trace(candlestick, row=i+1, col=1)

    fig.update_layout(height=600 * len(trade_data), title_text="Trade Data Candlestick Chart")
    st.plotly_chart(fig)


# Main function
if __name__ == '__main__':
    st.write("Let's build an awesome trading bot!!!")
    # Import settings.json
    project_settings = get_project_settings(import_filepath=settings_filepath)
    # Run through startup procedure
    startup = start_up(project_settings=project_settings)
    # Make it so that all columns are shown
    pd.set_option('display.max_columns', None)
    # If Startup successful, start trading while loop
    if startup:
        # Set a variable for the current time
        current_time = 0
        # Set a variable for previous time
        previous_time = 0
        # Specify the startup timeframe
        timeframe = project_settings["mt5"]["timeframe"]
        # Start while loop
        while True:
            # Get a value for current time. Use XAUUSD as it trades 24/7
            time_candle = mt5_lib.get_candlesticks(
                symbol="XAUUSD",
                timeframe=timeframe,
                number_of_candles=1
            )
            # Extract the time
            current_time = time_candle['time'][0]
            # Compare the current time against the previous time.
            if current_time != previous_time:
                # This means that a new candle has occurred. Proceed with strategy
                st.write("New Candle! Let's trade.")
                # Update previous time so that it is given the new current_time
                previous_time = current_time
                success, data = run_strategy(project_settings=project_settings)
                st.write(data)
                if success:
                    st.write("Strategy ran successfully.")
                    # Display the trade_data as a candlestick chart
                    display_trade_data(trade_data)
                else:
                    st.write("Error occurred while running the strategy.")
            else:
                # No new candle has occurred
                st.write("No new candle. Sleeping.")
                time.sleep(1)