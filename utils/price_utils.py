# utils/price_utils.py

import pandas as pd
import numpy as np

def calculate_returns(df):
    """
    Given a DataFrame with 'asset_id', 'date', and 'close', compute:
    - daily_pct_change
    - log_return
    Returns a DataFrame with new columns added.
    """
    df = df.sort_values(by=['asset_id', 'date'])
    df['daily_pct_change'] = df.groupby('asset_id')['close'].pct_change() * 100
    df['log_return'] = np.log(df['close'] / df.groupby('asset_id')['close'].shift(1))
    return df

def calculate_cumulative_return(df):
    """
    Adds a cumulative return column for each asset.
    """
    df = df.sort_values(by=['asset_id', 'date'])
    df['cumulative_return'] = (1 + df['daily_pct_change'] / 100).groupby(df['asset_id']).cumprod()
    return df
