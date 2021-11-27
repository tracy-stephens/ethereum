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

# data pipeline
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

#transactions
transactions_df['max_priority_fee_per_gas'] = transactions_df['max_priority_fee_per_gas'].fillna(0)

# reciepts
receipts_df.rename(columns={'receipt_cumulative_gas_used': 'cumulative_gas_used',
                            'receipt_gas_used': 'gas_used',
                            'receipt_status': 'status',
                            'receipt_effective_gas_price': 'effective_gas_price'
                           }, inplace=True)

cols = ['transaction_id', 'block_number', 'cumulative_gas_used',
    'gas_used', 'status', 'effective_gas_price']
receipts_df = receipts_df[cols]
# merge transactions and reciepts
transactions_receipts_df = transactions_df.merge(receipts_df,
                                             how='inner',
                                             left_on=['transaction_id', 'block_number'],
                                             right_on=['transaction_id', 'block_number'])

transactions_receipts_df[transactions_receipts_df.gas_price!=transactions_receipts_df.effective_gas_price]
# Calculate aggregated variables at block level
transactions_receipts_agg_df = transactions_receipts_df[['block_number', 'gas', 'gas_price', 'gas_used', 'effective_gas_price', 'max_priority_fee_per_gas']]\
        .groupby('block_number').agg(['min', 'mean', 'count'])
transactions_receipts_agg_df.columns = transactions_receipts_agg_df.columns.map('_'.join).str.strip('_')
# Keep only certain columns
transactions_receipts_agg_df = transactions_receipts_agg_df[['gas_min', 'gas_mean', 'gas_price_min', 'gas_price_mean', 
                                                            'gas_used_min', 'gas_used_mean', 'effective_gas_price_min',
                                                             'effective_gas_price_mean', 'effective_gas_price_count',
                                                            'max_priority_fee_per_gas_min', 'max_priority_fee_per_gas_mean']]
transactions_receipts_agg_df.rename(columns={'effective_gas_price_count': 'number_transactions_in_block'}, inplace=True)

pit_df = pd.read_csv(r'data/pit_60_rob.csv')
pit_df = pit_df.set_index('number')
pit_df.rename(columns={'lag_cutoff': 'lag_cutoff_60',
                       'latest_avail_block': 'latest_avail_60'},
             inplace=True)

merged_df = pit_df[['lag_cutoff_60', 'latest_avail_60', 'datetime']].merge(blocks_df,
                        how='inner',
                        left_index=True,
                        right_index=True)

pipeline_df = merged_df.merge(transactions_receipts_agg_df,
                        how='left',
                        left_index=True,
                        right_index=True)

# feature engineering
cols = ['gas_mean', 'gas_price_mean', 'gas_used_mean', 'effective_gas_price_mean', 'number_transactions_in_block', 'max_priority_fee_per_gas_mean']
for col in cols:
    # Last 5 blocks
    transactions_receipts_agg_df[col+'_pct_chg_last_5'] = transactions_receipts_agg_df[col]/transactions_receipts_agg_df[col].shift(5)-1
    # 25 blocks ago to 5 blocks ago percentage changes
    transactions_receipts_agg_df[col+'_pct_chg_last_25_to_5'] = transactions_receipts_agg_df[col].shift(5)/transactions_receipts_agg_df[col].shift(25)-1
    # 50 blocks ago to 5 blocks ago percentage changes
    transactions_receipts_agg_df[col+'_pct_chg_last_50_to_5'] = transactions_receipts_agg_df[col].shift(5)/transactions_receipts_agg_df[col].shift(50)-1
    # 100 blocks ago to 5 blocks ago percentage changes
    transactions_receipts_agg_df[col+'_pct_chg_last_100_to_5'] = transactions_receipts_agg_df[col].shift(5)/transactions_receipts_agg_df[col].shift(100)-1

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



