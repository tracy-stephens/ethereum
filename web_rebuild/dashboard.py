import numpy as np
import pandas as pd
import plotly_express as px
#import plotly.figure_factory as ff


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
    
    print(df.head())
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
            'Realized Gas Price' : 'black',
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
    
    chart_df = df
    chart_df.columns = [['Realized Gas Price', 'Predicted Gas Price']]
    df = chart_df.unstack().reset_index()
    df.columns = ['Name', 'Time', 'Value']
    
    fig = px.histogram(
        df, 
        x="Value", 
        #color="Name", 
        height=350,
        opacity=0.1,
        nbins=30,
        color_discrete_map={
            'Predicted Gas Price' : 'blue',
            'Realized Gas Price' : 'green'
        },
        labels={
            "Value": "Effective Gas Price",
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
        annotation_font_color="green"
    )
    fig.add_vline(
        x=chart_df[-1:][('Predicted Gas Price', )][0], 
        line_dash='dash', 
        line_color='blue',
        annotation_text="+1min Prediction",
        annotation_position="top right",
        annotation_font_color="blue"
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
    )
    fig.update_layout({
        'plot_bgcolor': 'rgba(0, 0, 0, 0)',
        'paper_bgcolor': 'rgba(0, 0, 0, 0)',
        'margin_t': 20
    })
    fig.update_layout(showlegend=False)
    return fig