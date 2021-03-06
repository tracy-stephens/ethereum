import numpy as np
import pandas as pd
import sys


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


def lagged_block_data(input_df, pit):

    df = input_df.copy()
    if df.index.name in ['number', 'block_number']:
        df = df.reset_index()

    if 'number' not in df.columns:
        df.columns = ['number' if i == 'block_number' else i for i in df.columns]

    # add 'latest_avail_block' column
    df = add_latest_avail_block(
        df,  # need to reset_index if the index is block_number
        pit,
        block_number_col='number'  # column name of the block_number column
    ).set_index('number')

    df = pd.merge(
        left=df,
        right=df,
        how='left',
        left_on='latest_avail_block',
        right_index=True,
        suffixes=('', '_lagged'),
        sort=True
    ).sort_index().filter(like='_lagged')

    return df.drop(columns='latest_avail_block_lagged')


def get_pit_blocks(blocks_df, lag):
    
    df = timestamp_to_datetime(blocks_df).sort_values(by='number')
    df['lag_cutoff'] = df['datetime'] - pd.offsets.DateOffset(seconds=lag)
    df['latest_avail_block'] = latest(df, 'number', 'datetime', 'lag_cutoff')
    df = df[[
        'number', 'datetime', 'lag_cutoff', 'latest_avail_block'
    ]].set_index('number').sort_index()

    return df


def transaction_id(df, index_col='transaction_index', block_number_col='block_number'):
    idx_str = df[index_col].astype(str).str.pad(
        width=6, side='left', fillchar='0'
    )
    blk_str = df[block_number_col].astype(str).str.pad(
        width=12, side='right', fillchar='0'
    )
    id_str = blk_str + idx_str
    return pd.Series(id_str.astype(int), name="transaction_id")


def get_size_gb(object_):
    return sys.getsizeof(object_) / (1024*1024*1024)