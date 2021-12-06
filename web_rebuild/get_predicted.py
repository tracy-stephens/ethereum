#!/usr/bin/python3

# get stuff
import pandas as pd
import numpy as np
import pickle
import xgboost
import os

def main():
    # filepath housekeeping
    dir_path = os.path.dirname(os.path.realpath(__file__))
    rf_final_model = os.path.join(dir_path, 'rf_final_model.pkl')
    xgb_final_model = os.path.join(dir_path, 'xgb_final_model.pkl')
    blocks = os.path.join(dir_path, 'blocks.csv')
    transactions = os.path.join(dir_path, 'transactions.csv')

    # load models
    with open(rf_final_model, 'rb') as rfm:
        rf = pickle.load(rfm)
    with open(xgb_final_model, 'rb') as xgbm:
        xgb = pickle.load(xgbm)

    # load data
    df = pd.read_csv(blocks)
    df2 = pd.read_csv(transactions)
    #df_history = st.cache(pd.read_csv)("history.csv")

    #################
    # data pipeline #
    #################

    df2_agg = df2[['block_timestamp', 'receipt_effective_gas_price', 'max_priority_fee_per_gas']].groupby('block_timestamp').agg(['mean', 'count'])
    df2_agg.columns = df2_agg.columns.map('_'.join).str.strip('_')
    df_merge = df.merge(right=df2_agg, how='inner', on='block_timestamp')
    df_merge = pd.DataFrame(df_merge).sort_values(by='block_timestamp', ascending=True)
    #df_merge = df_merge[-200:] # need 200 to do 100-ago division on last of 100 most recent

    cols = ['base_fee_per_gas', 'receipt_effective_gas_price_count', 'receipt_effective_gas_price_mean', 'max_priority_fee_per_gas_mean']
    for col in cols:
        # Last 5 blocks
        df_merge[col+'_pct_chg_last_5'] = df_merge[col]/df_merge[col].shift(5)-1
        # 100 blocks ago to 5 blocks ago percentage changes
        df_merge[col+'_pct_chg_last_100_to_5'] = df_merge[col].shift(5)/df_merge[col].shift(100)-1

    df_merge = df_merge[:-100] # only want those 100 most recent which have complete percents

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

    # one column needs to be renamed without killing the original columns name

    df_merge['latest_avail_gas_price_mean']  = df_merge['receipt_effective_gas_price_mean']

    # get only columns needed
    features = ['latest_avail_gas_price_mean',
                'base_fee_per_gas_pct_chg_last_100_to_5', 
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

    # winsorize: clip at 95th percentile value
    mask100 = (df_predict['max_priority_fee_per_gas_mean_pct_chg_last_100_to_5'] >= 17.677177)
    df_predict.loc[mask100, 'max_priority_fee_per_gas_mean_pct_chg_last_100_to_5'] = 17.677177
    mask5 = (df_predict['max_priority_fee_per_gas_mean_pct_chg_last_5'] >= 10.24462)
    df_predict.loc[mask5, 'max_priority_fee_per_gas_mean_pct_chg_last_5'] = 10.24462

    ###############
    # predictions #
    ###############

    #predicted = rf.predict(df_predict)
    rf_test_predictions = rf.predict(df_predict)
    xgb_test_pred = xgb.predict(xgboost.DMatrix(df_predict))
    
    ensemble_test_preds = (rf_test_predictions + 2 * xgb_test_pred) / 3

    ##################
    # output results #
    ##################

    chart = df_merge[['block_timestamp','receipt_effective_gas_price_mean']]
    chart['predicted'] = ensemble_test_preds
    chart.set_index('block_timestamp')
    chart.to_csv('chart.csv', index=False)

if __name__ == "__main__":
    main()
