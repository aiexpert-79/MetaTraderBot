import streamlit as st
import MetaTrader5 as mt5
import pandas as pd
from datetime import date, datetime
import plotly.graph_objects as go
import time
from plotly.subplots import make_subplots
from pynput.keyboard import Listener as KeyboardListener

TIMEFRAMES = ['M1', 'M5', 'M15', 'M30','H1', 'H4', 'D1', 'W1', 'MN1']
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
  
def rsi_fun(fig, rsi, df):
    periods = rsi_par
    close_delta = df['close'].diff()
    up = close_delta.clip(lower=0)
    down = -1*close_delta.clip(upper=0)
    ma_up = up.ewm(com = periods - 1, adjust=True, min_periods = periods).mean()
    ma_down = down.ewm(com = periods - 1, adjust=True, min_periods = periods).mean()
    rsi = ma_up / ma_down
    df['rsi'] = 100-(100/(1+rsi))
    
    fig.append_trace(go.Scatter(
        x=df['time'],
        y=df['rsi'],
        showlegend=False,
        marker={
        "color":"rgba(128,128,128,0.5)",
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
    if ma==True:
        df['ma']=df['open'].rolling(ma_par).mean()
        
        fig.add_trace(go.Scatter(
        x=df['time'],
        y=df['ma'],
        line=dict(color='firebrick', width=2)
        )
    )
        
    fig.layout.xaxis.fixedrange = True
    fig.layout.yaxis.fixedrange = True
    fig.update_layout(
        width=1200,
        height=700,
        margin=dict(l=20, r=20, t=20, b=20),
        paper_bgcolor="LightSteelBlue",
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
    
    if rsi==True:
        fig=rsi_fun(fig,rsi,df)
        
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
                fig=update_ohlc_chart(symbol, timeframe, candles, ma, rsi)
                st.plotly_chart(fig, use_container_width=True)
                time.sleep(1)
        
mt5.initialize()
keyboard_listener = KeyboardListener(on_press=on_press)
keyboard_listener.start()
candles = 30
# tab1, tab2, tab3 = st.tabs(["Main Trading", "Articles", "History"])

st.title('This is a Multi-Asset Trading Bot.')
c1, c2 = st.columns([1, 1])
ss = get_symbol_names()
# st.header("#Use + to zoom out and - to zoom in")
with c1:
    symbol = st.selectbox('Choose stock symbol', options=ss, index=1)

with c2:
    timeframe = st.selectbox('Choose time frame', options=['M1', 'M5', 'M15', 'M30','H1', 'H4', 'D1', 'W1', 'MN1'], index=1)
  
t1, t2 = st.columns([5,1])

with t1:
    placeholder = st.empty()
  
with t2:
    ma=st.selectbox('Activate moving average', options=[True, False], index=1)
    if ma:
        ma_par = st.number_input("Insert the simple moving average parameter", min_value=5, max_value=100, value=20)
    rsi = st.checkbox('Activate rsi')
    
    if rsi == True:
        rsi_par = st.number_input("Insert the rsi parameter", min_value=5, max_value=100, value=20)
        
    order_price = st.number_input("Insert a order value", min_value=0, max_value=10000, value=50)
    stop_loss = st.number_input("Insert a stop loss value", min_value=0, max_value=100, value=50)
    take_profit = st.number_input("Insert a take profit value", min_value=0, max_value=10000, value=1000)
    
runapp()
keyboard_listener.join()