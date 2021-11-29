import numpy as np
import pandas as pd
import plotly_express as px


def clean_dates(data, tz="US/Eastern"):
    """ data is a dict of dfs with keys blocks, transactions, and predicted """
    
    for k, v in data.items():
        v['block_timestamp'] = pd.to_datetime(v['block_timestamp'])
        v['block_timestamp'] = v['block_timestamp'].dt.tz_localize("UTC").dt.tz_convert(tz)

        if k != "transactions":
            v.set_index(v['block_timestamp'], inplace=True)
            v.drop(columns='block_timestamp', inplace=True)
    
    return data


def clean_predicted(df):
    
    preds_df = df.copy().sort_index().resample('s').ffill()
    preds_df = pd.concat([
        preds_df["receipt_effective_gas_price_mean"],
        pd.Series(
            preds_df['predicted'].values, 
            index=preds_df['predicted'].index + pd.offsets.Minute(),
            name="predicted"
        )
    ], axis=1)
    
    return preds_df


def surge_index(data, rolling_lookback='24h', quantile=0.25, halflife=15):
    
    normalized_data = data / data.rolling(rolling_lookback).quantile(quantile)
    idx = (np.log(normalized_data).clip(lower=0) + 1)
    smoothed_index = idx.ewm(halflife=halflife).mean()
    
    return smoothed_index[~data.isna()]


def surge_chart(df, stoplight_thresh = [1.5, 2]):
    
    chart_df = surge_index(df)
    chart_df.columns = [['Realized Gas Price', 'Predicted Gas Price']]
    chart_df = chart_df.unstack().reset_index()
    chart_df.columns = ['Name', 'Time', 'Value']
    
    fig = px.line(
        chart_df, 
        x='Time', 
        y='Value', 
        color='Name', 
        title='Surge Index',
        color_discrete_map={
            'Predicted Gas Price' : 'gray',
            'Realized Gas Price' : 'black'
        },
        line_dash='Name'
    )
    fig.add_hrect(
        y0=1,
        y1=stoplight_thresh[0],
        fillcolor="green",
        opacity=0.1,
        line_width=0,
    )
    fig.add_hrect(
        y0=stoplight_thresh[0],
        y1=stoplight_thresh[1],
        fillcolor="yellow",
        opacity=0.1,
        line_width=0,
    )
    fig.add_hrect(
        y0=stoplight_thresh[1],
        y1=max(chart_df['Value'].max(), 3),
        fillcolor="red",
        opacity=0.1,
        line_width=0,
    )
    fig.update_layout({
        'plot_bgcolor': 'rgba(0, 0, 0, 0)',
        'paper_bgcolor': 'rgba(0, 0, 0, 0)',
    })
    
    return fig