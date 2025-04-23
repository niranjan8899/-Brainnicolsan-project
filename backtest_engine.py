# utils/backtest_engine.py

import pandas as pd
import numpy as np

def prepare_data(price_df, asset_list, start_date, end_date):
    filtered = price_df[
        price_df['asset_id'].isin(asset_list) &
        price_df['date'].between(start_date, end_date)
    ]
    pivot = filtered.pivot(index='date', columns='asset_id', values='close')
    pivot = pivot.fillna(method='ffill').dropna()
    return pivot

def compute_portfolio_nav(price_data, weights):
    returns = price_data.pct_change().dropna()
    weight_array = np.array(weights) / 100
    portfolio_returns = returns.dot(weight_array)
    portfolio_nav = (1 + portfolio_returns).cumprod()
    return portfolio_nav

def compute_metrics(nav_series):
    days = (nav_series.index[-1] - nav_series.index[0]).days
    cagr = (nav_series.iloc[-1] ** (1 / (days / 365.25))) - 1
    max_dd = ((nav_series / nav_series.cummax()) - 1).min()
    return {
        'CAGR': cagr,
        'Max Drawdown': max_dd
    }
