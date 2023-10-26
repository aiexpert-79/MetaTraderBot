import streamlit as st
import MetaTrader5 as mt5
import pandas as pd
from datetime import date, datetime
import plotly.graph_objects as go
import time
import json
from plotly.subplots import make_subplots
from pynput.keyboard import Listener as KeyboardListener
import strategies.strategy_one as stra
import mt5_lib
from chatbot import predict

st.set_page_config(
    page_title="Real-Time MetaTrader Trading",
    page_icon="🧨",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://www.extremelycoolapp.com/help',
        'Report a bug': "https://www.extremelycoolapp.com/bug",
        'About': "# This is a header. This is an *extremely* cool app!"
    }
)

# Create the sidebar and add a tab selection widget
# st.image("logo.png", use_column_width=True)
selected_tab = st.sidebar.radio(label="**Trading**",
                                options=["Main Trading", "News", "History", "Chat Bot"],
                                label_visibility="hidden")
# Increase the size of the sidebar options
st.sidebar.markdown("""
    <style>
        label[data-baseweb="radio"]{ 
        background:linear-gradient(to bottom, #9d941c 0%, #000 100%);
        width:-webkit-fill-available;
        padding:20px;
        border-radius: 8px;
        }
    </style>
""", unsafe_allow_html=True)

# Implement tab events
if selected_tab == "Main Trading":
    with st.container():
        TIMEFRAMES = ['M1', 'M5', 'M15', 'M30', 'H1', 'H4', 'D1', 'W1', 'MN1']
        STRATEGIES = ['Long and Short Equity Strategy', 'Swing Trading', 'Scalping', 'Day Trading', 'Buy and Hold', 'Trend Trading', 'Value Investing']
        INDICATORS = ['RSI', 'EMA']
        TIMEFRAME_DICT = {
            'M1': mt5.TIMEFRAME_M1,
            'M5': mt5.TIMEFRAME_M5,
            'M15': mt5.TIMEFRAME_M15,
            'M30': mt5.TIMEFRAME_M30,
            'H1': mt5.TIMEFRAME_H1,
            'H4': mt5.TIMEFRAME_H4,
            'D1': mt5.TIMEFRAME_D1,
            'W1': mt5.TIMEFRAME_W1,
            'MN1': mt5.TIMEFRAME_MN1
        }

        def get_symbol_names():
            symbols = mt5.symbols_get()
            symbols_df = pd.DataFrame(symbols, columns=symbols[0]._asdict().keys())
            symbol_names = symbols_df["name"].tolist()
            return symbol_names

        def rsi_fun(fig, rsi, df):
            periods = rsi_par
            close_delta = df['close'].diff()
            up = close_delta.clip(lower=0)
            down = -1 * close_delta.clip(upper=0)
            ma_up = up.ewm(com=periods - 1, adjust=True, min_periods=periods).mean()
            ma_down = down.ewm(com=periods - 1, adjust=True, min_periods=periods).mean()
            rsi = ma_up / ma_down
            df['rsi'] = 100 - (100 / (1 + rsi))
            fig.append_trace(go.Scatter(
                x=df['time'],
                y=df['rsi'],
                showlegend=False,
                marker={
                    "color": "rgba(10,10,255,0.8)",
                },
            ), row=2, col=1)
            return fig

        def update_ohlc_chart(symbol, timeframe, bars, ma, rsi):
            timeframe = TIMEFRAME_DICT[timeframe]
            bars = int(bars)
            bars = mt5.copy_rates_from_pos(symbol, timeframe, 0, bars)
            df = pd.DataFrame(bars)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            fig = make_subplots(rows=2, cols=1, row_heights=[0.8, 0.2])
            fig.update(layout_showlegend=False)
            fig.append_trace(go.Candlestick(x=df['time'],
                                            open=df['open'],
                                            high=df['high'],
                                            low=df['low'],
                                            close=df['close']), row=1, col=1)
            if ma:
                df['ma'] = df['open'].rolling(ma_par).mean()
                fig.add_trace(go.Scatter(
                    x=df['time'],
                    y=df['ma'],
                    line=dict(color='firebrick', width=2)
                ))
            fig.layout.xaxis.fixedrange = True
            fig.layout.yaxis.fixedrange = True
            fig.update_layout(
                width=1200,
                height=700,
                margin=dict(l=20, r=20, t=20, b=20),
                paper_bgcolor="rgba(255,255,255,0.1)",
                xaxis=dict(
                    rangeslider=dict(visible=False),
                    type="date"
                )
            )
            fig.update_xaxes(
                rangebreaks=[
                    dict(bounds=["sat", "mon"]),
                    dict(values=["2015-12-25", "2016-01-01"])
                ], row=1, col=1
            )
            fig.add_hline(y=float(mt5.symbol_info_tick(symbol).bid), row=1, col=1)
            if rsi:
                fig = rsi_fun(fig, rsi, df)
            return fig

        def on_press(key):
            global candles
            if hasattr(key, 'char'):  # Check if the key object has the 'char' attribute
                if key.char == '+':
                    candles += 1
                elif key.char == '-':
                    candles -= 1

        def runapp():
            while True:
                with t1:
                    with placeholder.container():
                        fig = update_ohlc_chart(symbol, timeframe, candles, ma, rsi)
                        st.plotly_chart(fig, use_container_width=True)
                        time.sleep(1)

        mt5.initialize()
        keyboard_listener = KeyboardListener(on_press=on_press)
        keyboard_listener.start()
        candles = 30

        # # Set the default language to English
        # st.set_default_language('en')

        st.title('This is a Multi-Asset Trading Bot.')
        c1, c2, c3 ,c4= st.columns([1, 1, 1, 1])
        ss = get_symbol_names()
        with c1:
            symbol = st.selectbox('Choose stock symbol', options=ss, index=0)
        with c2:
            timeframe = st.selectbox('Choose time frame', options=TIMEFRAMES, index=0)
        with c3:
            strategy = st.selectbox('Choose Strategy', options=STRATEGIES, index=0)
        with c4:
            indicator = st.selectbox('Choose Indicator', options=INDICATORS, index=0)
            
        t1, t2 = st.columns([5, 1])
        with t1:
            placeholder = st.empty()
        with t2:
            ma = st.selectbox('Activate moving average', options=[True, False], index=1)
            if ma:
                ma_par = st.number_input("Insert the simple moving average parameter", min_value=10, max_value=200, value=20)
            rsi = st.checkbox('Activate RSI')
            if rsi:
                rsi_par = st.number_input("Insert the RSI parameter", min_value=5, max_value=100, value=20)
            order_price = st.number_input("Insert an order value", min_value=0, max_value=10000, value=50)
            stop_loss = st.number_input("Stop Loss (SL)", min_value=0, max_value=100, value=50)
            take_profit = st.number_input("Take Profit (TP)", min_value=0, max_value=10000, value=1000)
        runapp()
        keyboard_listener.join()

elif selected_tab == "News":
    st.title("News")
    
    # Define the articles
    articles = [
        {
            "title": "Article 1",
            "content": "This is the content of Article 1.",
        },
        {
            "title": "Article 2",
            "content": "This is the content of Article 2.",
        },
        {
            "title": "Article 3",
            "content": "This is the content of Article 3.",
        },
        {
            "title": "Article 4",
            "content": "This is the content of Article 4.",
        }
    ]
    
    # Display the articles in two rows
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader(articles[0]["title"])
        st.write(articles[0]["content"])
        
        st.subheader(articles[1]["title"])
        st.write(articles[1]["content"])
        
    with col2:
        st.subheader(articles[2]["title"])
        st.write(articles[2]["content"])
        
        st.subheader(articles[3]["title"])
        st.write(articles[3]["content"])
        

elif selected_tab == "History":
    with st.container():
        st.title("History")
        f = open("settings.json", "r")
        # Get the information from file
        project_settings = json.load(f)
        # Close the file
        f.close()
        symbol_for_strategy = project_settings['symbols'][0]
        # Set up a previous time variable
        previous_time = 0
        # Set up a current time variable
        current_time = 0
        # Start a while loop to poll MT5
        while True:
            # Retrieve the current candle data
            candle_data = mt5_lib.query_historic_data(symbol=symbol_for_strategy,
                                                            timeframe=project_settings['timeframe'], number_of_candles=1)
            # Extract the timedata
            current_time = candle_data[0][0]
            # Compare against previous time
            if current_time != previous_time:
                # Notify user
                print("New Candle")
                # Update previous time
                previous_time = current_time
                # Retrieve previous orders
                orders = mt5_lib.get_open_orders()
                # Cancel orders
                for order in orders:
                    mt5_lib.cancel_order(order)
                # Start strategy one on selected symbol
                stra.strategy_one(symbol=symbol_for_strategy, timeframe=project_settings['timeframe'],
                                    pip_size=project_settings['pip_size'])
            else:
                # Get positions
                positions = mt5_lib.get_open_positions()
                # Pass positions to update_trailing_stop
                for position in positions:
                    stra.update_trailing_stop(order=position, trailing_stop_pips=10,
                                                pip_size=project_settings['pip_size'])
            time.sleep(0.1)
            
elif selected_tab == "Chat Bot":
    st.title("I am a helpful trading assistant. please ask any trading-related questions.")

    user_input = st.text_input("🙋‍♂️ User Input")
    history = []  # Store history of messages

    if st.button("Send"):
        if user_input != "":
            history.append(("User", user_input))
            response = list(predict(user_input, history))
            assistant_response = response[-1]
            history.append(("Assistant", assistant_response))
            st.text_area("🤖 Trading Bot Response", value=assistant_response, height=100)