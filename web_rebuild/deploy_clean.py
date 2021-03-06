#!/home/ubuntu/.local/bin/streamlit
import streamlit as st
from streamlit_autorefresh import st_autorefresh
import pandas as pd
from dashboard import *
from datetime import datetime
import time

# fix streamlit layout
st.set_page_config(layout='wide')
st_autorefresh(interval=60000)

TZ = "US/Eastern"

@st.cache
def chart_data():
    day_df, hour_df = get_chart_data()
    return day_df, hour_df

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


minute_day_df, minute_hour_df = chart_data()

# charts
surge_cht = surge_chart(clean_predicted(data["predicted"]))
current_cht = gas_hist(data["predicted"])
minute_day_cht = minute_of_day_chart(minute_day_df)
minute_hour_cht = minute_of_hour_chart(minute_hour_df)
contract_cht = pct_smart_contract_chart(data["transactions"])
tip_cht = pct_tip_chart(data["transactions"])


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
last_pred, recommendation, stoplight_markdown = stoplight(data["predicted"])

# make sidebar
st.sidebar.title('Ethereum Stoplight')
#st.sidebar.header('Applied Machine Learning')
st.sidebar.subheader('Ethereum Transaction Price Estimator')

menu = st.sidebar.radio(
    "View",
    ("Stoplight", "Time Patterns", "Recent Transactions"),
)

st.sidebar.markdown('Current ethereum gas price estimators either use simple historical price trends or settle for limited supply-side (miner) data to guess a potentially successful transaction fee.')
st.sidebar.markdown('Ethereum Stoplight applies machine learning to gigabytes and gigabytes of historical transaction-level and block-level smart contracts activity data to accurately predict the current required fee to successfully get your transaction added to the next block.')

if menu == 'Stoplight':
    col1, col2 = st.columns([1,2])
    with col1:
        st.markdown('**Current Predicted Gas Price:**')
        st.markdown(stoplight_markdown , unsafe_allow_html = True)
        st.markdown(recommendation)

    with col2:
        st.markdown('**Surge Index**')
        st.plotly_chart(surge_cht)

    st.markdown('**Current Prediction Compared to Last Block Average** (blue vs green dotted line)')
    st.markdown('Histograms illustrate data underlying dotted lines (high outliers may drive Last Block Average dotted line off-center)')    
    st.plotly_chart(current_cht)
        
if menu == 'Time Patterns':
    st.markdown('**Surge History: Surge Patterns by Time of Day**')
    st.markdown('A Significant Persistent Surge Occurs Daily at Midnight EST. We Hypothesize These Are Due to Smart Contract Programming.<br>Surges and Spikes Also Tend to Form in the EST Evening. Standard Gas Price Variability Can Be Observed During EST Business Hours.<br>Gas Prices Tend to Be Low During Early Morning Hours EST.', unsafe_allow_html=True) 
    st.plotly_chart(minute_day_cht)
    st.markdown('**Surge History: Surge Patterns by Minute of the Hour**')
    st.markdown('Highest Surges Typically Are Observed at Beginning (First 5 Minutes) and End of the Hour and More Surges at Beginning of the Hour') 
    st.plotly_chart(minute_hour_cht)

if menu == 'Recent Transactions':
    st.markdown('**Percent of Transactions Per Block in Last Hour Which Were Smart Contracts**')
    st.plotly_chart(contract_cht)
    st.markdown('**Percent of Transactions Per Block in Last Hour Requiring Additional Gas Tip Payment to Be Included in Block**')
    st.plotly_chart(tip_cht)

 




