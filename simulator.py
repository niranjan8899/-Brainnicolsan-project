# utils/simulator.py

import pandas as pd
import statsmodels.api as sm

def get_correlated_proxies(price_data, target_asset, proxy_assets):
    """
    Returns a list of (proxy_asset, correlation) tuples ranked by absolute correlation
    of log returns with the target asset.
    """
    correlations = []
    target_df = price_data[price_data['asset_id'] == target_asset][['date', 'log_return']].rename(columns={'log_return': 'log_return_target'})

    for proxy in proxy_assets:
        proxy_df = price_data[price_data['asset_id'] == proxy][['date', 'log_return']].rename(columns={'log_return': 'log_return_proxy'})
        merged = pd.merge(target_df, proxy_df, on='date')
        if not merged.empty:
            corr = merged['log_return_target'].corr(merged['log_return_proxy'])
            correlations.append((proxy, corr))

    return sorted(correlations, key=lambda x: abs(x[1]), reverse=True)

def run_log_return_regression(price_data, target_asset, proxy_asset):
    """
    Performs linear regression of target log returns ~ proxy log returns.
    Returns fitted model and merged DataFrame.
    """
    target_df = price_data[price_data['asset_id'] == target_asset][['date', 'log_return']].rename(columns={'log_return': 'log_return_target'})
    proxy_df = price_data[price_data['asset_id'] == proxy_asset][['date', 'log_return']].rename(columns={'log_return': 'log_return_proxy'})
    merged_df = pd.merge(target_df, proxy_df, on='date').dropna()

    X = merged_df['log_return_proxy']
    y = merged_df['log_return_target']
    X = sm.add_constant(X)
    model = sm.OLS(y, X).fit()

    return model, merged_df
