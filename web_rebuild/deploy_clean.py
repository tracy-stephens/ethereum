#!/home/ubuntu/.local/bin/streamlit
import streamlit as st
from streamlit_autorefresh import st_autorefresh
import pandas as pd
from dashboard import (
    clean_dates,
    clean_predicted,
    surge_chart,
    surge_index,
    gas_hist,
    pct_tip_chart,
    minute_of_day_chart,
    minute_of_hour_chart,
    pct_smart_contract_chart
)
from datetime import datetime
import time

# fix streamlit layout
st.set_page_config(layout='wide')

st_autorefresh(interval=60000)

TZ = "US/Eastern"
    
files = {
    "blocks" : 'blocks.csv',
    "transactions" : 'transactions.csv',
    "predicted" : 'chart.csv'
}

try: # when new csv's are being generated by cron, they cannot be loaded,resulting in an error
    data_raw = {k : pd.read_csv(v) for k, v in files.items()}
except:
    wait = st.empty() # .empty() allows to remove the element once it has fulfilled its use
    wait.subheader("Please wait... occasionally, refreshing data can cause short delays")
    time.sleep(20)
    wait.empty()
    data_raw = {k : pd.read_csv(v) for k, v in files.items()}

data = clean_dates(data_raw, tz=TZ) 

# charts
surge_cht = surge_chart(clean_predicted(data["predicted"]))
current_cht = gas_hist(data["predicted"])

# fix overhead padding
padding = 1
st.markdown(
    f""" 
    <style>

    .reportview-container .main .block-container{{
        padding-top: 0;
        padding-right: {padding}rem;
        padding-left: {padding}rem;
        padding-bottom: {padding}rem;
        }} 

    .reportview-container .css-1lcbmhc .css-1d391kg {{
        padding-top: {padding}rem;
        padding-right: {padding}rem;
        padding-left: {padding}rem;
        padding-bottom: {padding}rem;
        }}

    .element-container .stPlotlyChart .plot-container .user-select-none{{
        padding-top: {padding}rem;
        padding-right: {padding}rem;
        padding-left: {padding}rem;
        padding-bottom: {padding}rem;
        }}
    
    .css-1d391kg {{
        width: 14rem;
        }}

    </style> 
    """, 
    unsafe_allow_html=True)

# core website content
last_pred = str(round(data["predicted"].iloc[-1][1]/1000000000))
low = 'rgba(230,242,231)'
med = 'rgba(255,255,220)'
hi = 'rgba(255,231,233)'

# get surge color cutoffs
thresh_df = surge_index(data["predicted"])
thresh_df.columns = [['Realized Gas Price', 'Predicted Gas Price']]
thresh_df = thresh_df.unstack().reset_index()
thresh_df.columns = ['Name', 'Time', 'Value']
thresh = thresh_df['Value'].iloc[-1]

if thresh <= 1.5:
    surge_color = low
    recommendation = "Stoplight is Green: We recommend executing your transaction now, transaction fees are currently low."
elif thresh > 1.5 and thresh <= 2.0:
    surge_color = med
    recommendation = "Stoplight is Yellow: Transaction fees are currently slightly higher than normal. You could do better, but if you must execute your transaction, it is not a bad time to do so."
elif thresh > 2.0:
    surge_color = hi
    recommendation = "Stoplight is Red: We recommend waiting to execute your transaction, transaction fees are currently high."

# define stoplight
circle = '<style>.circle {width: 200px; height: 200px; line-height: 200px; margin-left: 20px; border-radius: 50%; font-size: 20px; color: #000; text-align: center; background:' + surge_color + '}</style>' + '<div class="circle">' + last_pred + 'B gwei</div>'

# make sidebar
st.sidebar.title('Ethereum Stoplight')
#st.sidebar.header('Applied Machine Learning')
st.sidebar.subheader('Ethereum Transaction Price Estimator')
st.sidebar.markdown('Current ethereum gas price estimators either use simple historical price trends or settle for limited supply-side (miner) data to guess a potentially successful transaction fee.')
st.sidebar.markdown('Ethereum Stoplight applies machine learning to gigabytes and gigabytes of historical transaction-level and block-level smart contracts activity data to accurately predict the current required fee to successfully get your transaction added to the next block.')

col1, col2 = st.columns([1,2])


with col1:
    st.markdown('**Current predicted gas price:**')
    st.markdown(circle, unsafe_allow_html = True)
    st.markdown(recommendation)
    st.plotly_chart(current_cht)
    st.plotly_chart(minute_of_day_chart(data["blocks"]))
    st.plotly_chart(minute_of_hour_chart(data["blocks"]))
    st.plotly_chart(pct_smart_contract_chart(data["transactions"]))
    st.plotly_chart(pct_tip_chart(data["transactions"]))
    
with col2:
    st.markdown('**Surge Index**')
    st.plotly_chart(surge_cht)
    
    



