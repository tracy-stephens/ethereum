import numpy as np
import pandas as pd


def latest(input_df, target_col, ref_date_col, limit_date_col):
    """ get the latest availabale of a column """

    df = input_df[[target_col, ref_date_col, limit_date_col]].sort_values(by=ref_date_col)
    start = df[ref_date_col].min()

    res = {
        k : df[target_col][df[ref_date_col] < v].values[-1] if v > start else np.nan
        for k, v in df[limit_date_col].to_dict().items()
    }

    return pd.Series(res)


def timestamp_to_datetime(input_df, timestamp_col='timestamp'):

    # readible date column for blocks
    df = input_df
    df = df.assign(datetime=pd.to_datetime(df[timestamp_col], unit='s').values)
    df.drop(timestamp_col, axis=1, inplace=True)

    return df


def lead_lag(x, y, lags):

    corr_ = {}
    for i in lags:
        corr_[i] = x.corrwith(y.shift(i))[0]
    return pd.Series(corr_)


def add_latest_avail_block(df, pit, block_number_col='block_number'):
    res = pd.merge(
        left=df,
        right=pit[['latest_avail_block']],
        how='left',
        left_on=block_number_col,
        right_index=True
    )
    return res