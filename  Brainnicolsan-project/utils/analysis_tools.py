# utils/analysis_tools.py

import numpy as np
import pandas as pd

def compute_advanced_metrics(nav_series, risk_free_rate=0.01):
    """
    Computes advanced portfolio performance metrics:
    - CAGR
    - Max Drawdown
    - Volatility (annualized)
    - Sharpe Ratio (annualized)
    
    Parameters:
    - nav_series: cumulative NAV series
    - risk_free_rate: annual risk-free rate (default 1%)
    
    Returns:
    - Dictionary of metrics
    """
    returns = nav_series.pct_change().dropna()
    nav = nav_series.dropna()
    days = (nav.index[-1] - nav.index[0]).days
    years = days / 365.25

    cagr = (nav.iloc[-1] ** (1 / years)) - 1
    max_dd = ((nav / nav.cummax()) - 1).min()
    volatility = returns.std() * np.sqrt(252)
    sharpe = (returns.mean() * 252 - risk_free_rate) / (returns.std() * np.sqrt(252))

    return {
        "CAGR": cagr,
        "Max Drawdown": max_dd,
        "Volatility": volatility,
        "Sharpe Ratio": sharpe
    }

def compare_multiple_portfolios(nav_dict, risk_free_rate=0.01):
    """
    Computes advanced metrics for multiple portfolios
    
    Parameters:
    - nav_dict: dict of {portfolio_name: NAV_series}
    
    Returns:
    - DataFrame of metrics
    """
    results = []
    for name, nav in nav_dict.items():
        metrics = compute_advanced_metrics(nav, risk_free_rate)
        results.append({"Portfolio": name, **metrics})
    return pd.DataFrame(results).set_index("Portfolio")
