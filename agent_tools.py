# utils/agent_tools.py

import pandas as pd
import numpy as np

def get_portfolio_list(nav_df):
    return list(nav_df.columns) if not nav_df.empty else []

def get_portfolio_metrics(nav_series):
    returns = nav_series.pct_change().dropna()
    cagr = (nav_series.iloc[-1] ** (1 / ((nav_series.index[-1] - nav_series.index[0]).days / 365.25))) - 1
    max_dd = ((nav_series / nav_series.cummax()) - 1).min()
    volatility = returns.std() * np.sqrt(252)
    sharpe = (returns.mean() * 252 - 0.01) / (returns.std() * np.sqrt(252))
    return {
        "CAGR": f"{cagr:.2%}",
        "Max Drawdown": f"{max_dd:.2%}",
        "Volatility": f"{volatility:.2%}",
        "Sharpe Ratio": f"{sharpe:.2f}"
    }

def compare_two_portfolios(nav_df, p1, p2):
    metrics_1 = get_portfolio_metrics(nav_df[p1])
    metrics_2 = get_portfolio_metrics(nav_df[p2])
    return pd.DataFrame({p1: metrics_1, p2: metrics_2})

def describe_asset(asset_id, metadata_df):
    row = metadata_df[metadata_df['asset_id'] == asset_id]
    if row.empty:
        return f"No information available for asset '{asset_id}'."
    else:
        info = row.iloc[0]
        return f"**{info['name']}** ({info['code']}) on {info['exchange']}\n\nType: {info['asset_type']}\nCategory: {info['category']}\nCurrency: {info['currency_code']}\nDescription: {info['description']}"
