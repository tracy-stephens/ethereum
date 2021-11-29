# get stuff
import streamlit as st
import pandas as pd
import numpy as np
import plotly_express as px
import pickle

# load model
with open('rf_test_model.pkl', 'rb') as model:
    rf = pickle.load(model)

# load data
df = pd.read_csv("blocks.csv")
df2 = pd.read_csv("transactions.csv")
df_history = st.cache(pd.read_csv)("history.csv")

#################
# data pipeline #
#################

df2_agg = df2[['block_timestamp', 'receipt_effective_gas_price', 'max_priority_fee_per_gas']].groupby('block_timestamp').agg(['mean', 'count'])
df2_agg.columns = df2_agg.columns.map('_'.join).str.strip('_')
df_merge = df.merge(right=df2_agg, how='inner', on='block_timestamp')
df_merge = pd.DataFrame(df_merge).sort_values(by='block_timestamp', ascending=True)
df_merge = df_merge[-200:] # need 200 to do 100-ago division on last of 100 most recent

cols = ['base_fee_per_gas', 'receipt_effective_gas_price_count', 'receipt_effective_gas_price_mean', 'max_priority_fee_per_gas_mean']
for col in cols:
    # Last 5 blocks
    df_merge[col+'_pct_chg_last_5'] = df_merge[col]/df_merge[col].shift(5)-1
    # 100 blocks ago to 5 blocks ago percentage changes
    df_merge[col+'_pct_chg_last_100_to_5'] = df_merge[col].shift(5)/df_merge[col].shift(100)-1

df_merge = df_merge[-100:] # only want those 100 most recent which have complete percents

# datetime dummy variables
df_merge['local_date'] = pd.to_datetime(df_merge['block_timestamp']).dt.tz_localize('utc').dt.tz_convert('US/Eastern')
df_merge['date'] = df_merge['local_date'].dt.date
df_merge['hour'] = df_merge['local_date'].dt.hour
df_merge['minute'] = df_merge['local_date'].dt.minute
df_merge['weekday'] = df_merge['local_date'].dt.weekday

df_merge['hour_dummy'] = 0
start_hour = 2
end_hour = 9
mask = (df_merge['hour'] < start_hour) | (df_merge['hour'] > end_hour)
df_merge.loc[mask, 'hour_dummy'] = 1

df_merge['minute_dummy'] = 0
start_minute = 1
end_minute = 6
mask = (df_merge['minute'] >= start_minute) & (df_merge['minute'] <= end_minute)
df_merge.loc[mask, 'minute_dummy'] = 1

df_merge['weekday_dummy'] = 0
start_weekday = 1
end_weekday = 4
mask = (df_merge['weekday'] >= start_weekday) & (df_merge['weekday'] <= end_weekday)
df_merge.loc[mask, 'weekday_dummy'] = 1

#rename key columns to match the model's expectations
df_merge.rename(columns={
       'receipt_effective_gas_price_count_pct_chg_last_5':'number_transactions_in_block_pct_chg_last_5',
       'receipt_effective_gas_price_count_pct_chg_last_100_to_5':'number_transactions_in_block_pct_chg_last_100_to_5',
       'receipt_effective_gas_price_mean_pct_chg_last_5':'effective_gas_price_mean_pct_chg_last_5',
       'receipt_effective_gas_price_mean_pct_chg_last_100_to_5':'effective_gas_price_mean_pct_chg_last_100_to_5',
        }, inplace=True)

# get only columns needed
features = ['base_fee_per_gas_pct_chg_last_100_to_5', 
            'base_fee_per_gas_pct_chg_last_5',
            'number_transactions_in_block_pct_chg_last_100_to_5', 
            'number_transactions_in_block_pct_chg_last_5',
            'effective_gas_price_mean_pct_chg_last_100_to_5', 
            'effective_gas_price_mean_pct_chg_last_5',
            'max_priority_fee_per_gas_mean_pct_chg_last_100_to_5', 
            'max_priority_fee_per_gas_mean_pct_chg_last_5',
            'minute_dummy', 'hour_dummy', 'weekday_dummy'
            ]
df_predict = df_merge[features]

# psuedo-winsorize: swap out infs with 95th percentile value (generated during % change step if denominator is 0)
columns = df_predict.columns
values = [0.431637, 0.309303, 8.809524, 8.9, 17.677177, 16.710033, 15.495496, 10.24462]
for i in columns[:8]:
    df_predict[i].replace(np.inf, values[columns.get_loc(i)], inplace=True)

###############
# predictions #
###############

predicted = rf.predict(df_predict)


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



