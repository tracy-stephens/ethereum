import numpy as np
import pandas as pd
import plotly_express as px
import streamlit as st
#import plotly.figure_factory as ff


def stoplight(df):
    last_pred = str(round(df.iloc[-1][1]/1000000000))
    low = 'rgba(230,242,231)'
    med = 'rgba(255,255,220)'
    hi = 'rgba(255,231,233)'
    
    thresh_df = surge_index(df.copy())
    thresh_df.columns = [['Realized Gas Price', 'Predicted Gas Price']]
    thresh_df = thresh_df.unstack().reset_index()
    thresh_df.columns = ['Name', 'Time', 'Value']
    thresh = thresh_df['Value'].iloc[-1]
    
    if thresh <= 1.5:
        surge_color = low
        recommendation = "Stoplight is Green - Transaction fees are currently low."
    elif thresh > 1.5 and thresh <= 2.0:
        surge_color = med
        recommendation = "Stoplight is Yellow - Transaction fees are currently slightly higher than normal."
    elif thresh > 2.0:
        surge_color = hi
        recommendation = "Stoplight is Red - Transaction fees are currently high."
    
    # define stoplight
    circle = '<style>.circle {' + \
        'width: 200px; height: 200px; line-height: 200px; border:2px solid black; ' + \
        'margin-left: 20px; border-radius: 50%; font-size: 20px; ' + \
        'color: #000; text-align: center; background:' + \
        surge_color + '}</style>' + '<div class="circle">' + last_pred + 'B gwei</div>'
    
    return last_pred, recommendation, circle


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
    
    chart_df = surge_index(df).copy()
    chart_df.columns = [['Realized Gas Price', 'Predicted Gas Price']]
    chart_df = chart_df.unstack().reset_index()
    chart_df.columns = ['Name', 'Time', 'Value']
    
    fig = px.line(
        chart_df, 
        x='Time', 
        y='Value', 
        color='Name', 
        height=350,
        #title='Surge Index',
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
        'margin_t': 20,
    })
    
    return fig


def gas_hist(df):
    
    chart_df = df
    chart_df.columns = [['Realized Gas Price', 'Predicted Gas Price']]
    df = chart_df.unstack().reset_index()
    df.columns = ['Name', 'Time', 'Value']
    
    fig = px.histogram(
        df, 
        x="Value", 
        color="Name", 
        opacity=0.1,
        nbins=30,
        height=500,
        width=1000,
        color_discrete_map={
            'Predicted Gas Price' : 'green',
            'Realized Gas Price' : 'blue'
        },
        #marginal="violin",
        title="Current Prediction"
    )
    fig.add_vline(
        x=chart_df[-1:][('Realized Gas Price', )][0], 
        line_dash='dash',
        line_color='green',
        annotation_text="Last Block Avg.",
        annotation_position="bottom right",
        annotation_font_color="green",
        annotation_font_size=16
    )
    fig.add_vline(
        x=chart_df[-1:][('Predicted Gas Price', )][0], 
        line_dash='dash', 
        line_color='blue',
        annotation_text="+1min Prediction",
        annotation_position="top right",
        annotation_font_color="blue",
        annotation_font_size=16,
    )
    fig.update_layout({
        'plot_bgcolor': 'rgba(0, 0, 0, 0)',
        #'margin_t': 20
    })
    #fig.update_layout(showlegend=False)
    
    return fig


def pct_tip_chart(df):
    has_tip = df.groupby([
        df["max_priority_fee_per_gas"] == 0, 
        df["block_timestamp"]
    ]).count()["max_priority_fee_per_gas"].unstack(0)
    has_tip_pct = has_tip[True] / (has_tip.sum(1))
    fig = px.area(
        has_tip_pct.rolling(5).mean(), 
        height=400,
        width=1000,
        title='% of Included Transactions With Tip by Block'
    )
    fig.update_layout({
        'plot_bgcolor': 'rgba(0, 0, 0, 0)',
        'paper_bgcolor': 'rgba(0, 0, 0, 0)',
    })
    fig.update_layout(showlegend=False)
    return fig


def get_pct_smart_contract(df):
    counts = df.copy().groupby(
        by=[df['block_timestamp'], df['receipt_gas_used'] > 21000]
    ).count()
    counts_df = counts['receipt_gas_used'].unstack()
    counts_df['pct_smart_contract'] = counts_df[True] / counts_df.sum(1)
    return counts_df['pct_smart_contract']


def pct_smart_contract_chart(df):
    chart_df = get_pct_smart_contract(df)
    fig = px.area(
        chart_df.rolling(5).mean(), 
        height=400,
        width=1000,
        title='% Smart Contracts'
    )
    fig.update_layout({
        'plot_bgcolor': 'rgba(0, 0, 0, 0)',
        'paper_bgcolor': 'rgba(0, 0, 0, 0)',
    })
    fig.update_layout(showlegend=False)
    return fig


def get_bspg_by_minute(df):
    blocks = df.copy()
    
    blocks['hour'] = blocks.index.hour
    blocks['minute_time'] = blocks.index.floor('Min').time

    bspg_grouper = blocks[['minute_time', 'hour', 'base_fee_per_gas']].groupby(['minute_time'])
    bspg_data = pd.DataFrame({
        "mean" : bspg_grouper.mean()['base_fee_per_gas'],
        "90th %ile" : bspg_grouper.quantile(0.9)['base_fee_per_gas'],
        "95th %ile" : bspg_grouper.quantile(0.95)['base_fee_per_gas'],
        "max" : bspg_grouper.max()['base_fee_per_gas']
    })
    bspg_data.index = pd.to_datetime(bspg_data.index, format='%H:%M:%S')
    return bspg_data


def minute_of_day_chart(df, stoplight_thresh = [1.5, 2]):
    bspg_data = get_bspg_by_minute(surge_index(df))
    fig = px.line(
        bspg_data,
        title='Surge by Time of Day',
        height=350,
        #width=1000
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
        y1=max(bspg_data['max'].max(), 3),
        fillcolor="red",
        opacity=0.1,
        line_width=0,
    )
    fig.update_layout({
        'plot_bgcolor': 'rgba(0, 0, 0, 0)',
        'paper_bgcolor': 'rgba(0, 0, 0, 0)',
        'margin_t': 20,
    })
    return fig


def get_bspg_over_hour(df):
    blocks = df.copy()
    blocks['minute'] = blocks.index.minute
    bspg_grouper = blocks[['minute', 'base_fee_per_gas']].groupby(['minute'])
    bspg_data = pd.DataFrame({
        "mean" : bspg_grouper.mean()['base_fee_per_gas'],
        "90th %ile" : bspg_grouper.quantile(0.9)['base_fee_per_gas'],
        "95th %ile" : bspg_grouper.quantile(0.95)['base_fee_per_gas'],
        "max" : bspg_grouper.max()['base_fee_per_gas'],
    })
    return bspg_data


def minute_of_hour_chart(df, stoplight_thresh = [1.5, 2]):
    bspg_data = get_bspg_over_hour(surge_index(df))
    fig = px.line(
        bspg_data,
        title='Surge by Minute of Hour',
        height=350,
        #width=500
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
        y1=max(bspg_data['max'].max(), 3),
        fillcolor="red",
        opacity=0.1,
        line_width=0,
    )
    fig.update_layout({
        'plot_bgcolor': 'rgba(0, 0, 0, 0)',
        'paper_bgcolor': 'rgba(0, 0, 0, 0)',
        'margin_t': 20,
    })
    return fig