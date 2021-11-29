# get stuff
import streamlit as st
import pandas as pd
import numpy as np
import plotly_express as px

###########
# website #
###########

# fix streamlit layout
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



