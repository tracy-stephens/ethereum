import numpy as np
import pandas as pd
import plotly_express as px
import streamlit as st
from datetime import datetime
#import plotly.figure_factory as ff


def get_chart_data():
    day_path = 'chart_data/minute_day.csv'
    hour_path = 'chart_data/minute_hour.csv'
    
    day_df = pd.read_csv(day_path, index_col=0)
    day_df.index = [datetime.strptime(i, '%H:%M:%S').time() for i in day_df.index]
    
    hour_df = pd.read_csv(hour_path, index_col=0)

    return day_df, hour_df
    

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
    
    new_data = {}
    for k, v in data.items():
        df = v.copy()
        df['block_timestamp'] = pd.to_datetime(df['block_timestamp'])
        df['block_timestamp'] = df['block_timestamp'].dt.tz_localize("UTC").dt.tz_convert(tz)
        new_data[k] = df

        if k != "transactions":
            new_data[k].set_index(df['block_timestamp'], inplace=True)
            new_data[k].sort_index(inplace=True)
            new_data[k].drop(columns='block_timestamp', inplace=True)

    return new_data


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
        labels={
            "Time": "Block (timestamp)",
            "Value": "Gas Price Surge Multiple",
            'Name' : ''
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
    
    chart_df = df.copy()
    chart_df.columns = [['Realized Gas Price', 'Predicted Gas Price']]
    df = chart_df.unstack().reset_index()
    df.columns = ['Name', 'Time', 'Value']

    fig = px.histogram(
        df, 
        x="Value", 
        color="Name", 
        opacity=0.1,
        nbins=30,
        height=350,
        color_discrete_map={
            'Predicted Gas Price' : 'blue',
            'Realized Gas Price' : 'green'
        },
        labels={
            "Value": "Effective Gas Price",
            "Name": "",
        },
        #marginal="violin",
        #title="Current Prediction"
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
        'yaxis_title' : "Number of Recent Blocks",
        'margin_t': 20
    })
    fig.update_xaxes(range=[0, 400000000000])

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
        height=350,
        #title='% of Included Transactions With Tip by Block'
        labels={
            "value": "Percent Requiring Tip",
            "block_timestamp": "Block (timestamp)",
        },
    )
    fig.update_layout({
        'plot_bgcolor': 'rgba(0, 0, 0, 0)',
        'paper_bgcolor': 'rgba(0, 0, 0, 0)',
        'margin_t': 20
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
        height=350,
        #title='% Smart Contracts'
        labels={
            "value": "Percent Smart Contracts",
            "block_timestamp": "Block (timestamp)",
        },
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
    bspg_data.index = bspg_data.index.floor('Min').time
    return bspg_data


def minute_of_day_chart(df, stoplight_thresh = [1.5, 2]):
    bspg_data = df
    #bspg_data = get_bspg_by_minute(surge_index(df))
    fig = px.line(
        bspg_data,
        #title='Surge by Time of Day',
        height=350,
        #width=1000
        labels={
            "value": "Gas Price Surge Multiple",
            "minute_time": "Hour of the Day",
            "variable": "",
        },
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
        y1=max(df['max'].max(), 3),
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
    bspg_data = df
    #bspg_data = get_bspg_over_hour(surge_index(df))
    fig = px.line(
        df,
        #title='Surge by Minute of Hour',
        height=350,
        #width=500
        labels={
            "value": "Gas Price Surge Multiple",
            "minute": "Minute of the Hour",
            "variable": "",
        },
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
        y1=max(df['max'].max(), 3),
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