#get stuff
import streamlit as st
import pandas as pd
import numpy as np
import plotly_express as px

st.set_page_config(layout='wide')
# fix overhead padding
padding = 1
st.markdown(f""" <style>

    .reportview-container .main .block-container{{
        padding-top: {padding}rem;
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

    </style> 
    """, 
    unsafe_allow_html=True)

# make sidebar
st.sidebar.title('Effector.io')
st.sidebar.header('Applied Machine Learning')
st.sidebar.subheader('Ethereum Dashboard & Gas Price Predictions')
st.sidebar.markdown('Current ethereum gas price estimators either use simple historical price trends or settle for limited available and biased supply-side (miner) data to guess a potentially successful "tip".')
st.sidebar.markdown('Effector.io applies machine learning to gigabytes and gigabytes of historical transaction-level and block-level smart contracts activity data to accurately predict the current required "tip" to successfully get your transaction added to the next block.')

df1 = st.cache(pd.read_csv)("daily_mean_base_fee_per_gas.csv")
df2 = st.cache(pd.read_csv, allow_output_mutation=True)("txn_2_blx.csv")
df3 = st.cache(pd.read_csv)("miners.csv")
# convert datetime to datetime
df2['time'] = pd.to_datetime(df2['time'], format='%Y-%m-%d %H:%M:%S')

# chart of recent average daily gas prices
fig1 = px.line(
	df1, 
	x ='date',
	y='base_fee_per_gas_mean', 
	title='ETH Daily Avg Gas Price Last Mo',
	height=300,
	labels={
		"date": "",
        "base_fee_per_gas_mean": "Gas Price (Gwei)",
        },
	)

fig1.update_layout(
	title_font_size=24,
	)

# chart of gas prices showing spikes on 8/14
dftemp = df2[df2['time']>'2021-08-14 16']
fig2 = px.line(
	dftemp, 
	x='time', 
	y='gas_price', 
	title="Recent ETH Gas Price", 
	height=300,
	labels={
		"time": "",
        "gas_price": "Gas Price (Gwei)",
        },
    log_y=True,
	)

fig2.update_layout(
	title_font_size=24,
	)
# chart of transactions per block showing dips on 8/14
fig3 = px.line(
	dftemp, 
	x='time', 
	y='count', 
	title="Transactions Per Block",
	height=300,
	labels={
		"time": "",
        "count": "Transactions/Block",
        },
	)

fig3.update_layout(
	title_font_size=24,
	)

fig4 = px.line(
	dftemp, 
	x='time', 
	y='gas', 
	title="Gas Needed Per Block",
	height=300,
	labels={
		"time": "",
        "gas": "Gas/Block (Gwei)",
        },
    #log_y=True,
	)

fig4.update_layout(
	title_font_size=24,
	)

col1, col2 = st.columns(2) 

with col2:
	st.plotly_chart(fig1, use_container_width=True)
	st.markdown('#### Top miners in last month')
	st.table(df3)
with col1:
	st.plotly_chart(fig2, use_container_width=True)
	st.plotly_chart(fig4, use_container_width=True)
	st.plotly_chart(fig3, use_container_width=True)

