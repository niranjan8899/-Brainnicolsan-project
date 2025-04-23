# utils/data_cleaner.py

import pandas as pd
from scipy.stats import zscore

def detect_missing_data(df, max_gap_days=6):
    """
    Detect assets with gaps in trading data greater than max_gap_days.
    Returns list of asset_ids with such gaps.
    """
    missing_assets = []
    for asset_id, group in df.groupby("asset_id"):
        sorted_dates = group['date'].sort_values()
        gaps = sorted_dates.diff().dt.days.fillna(1)
        if (gaps > max_gap_days).any():
            missing_assets.append(asset_id)
    return missing_assets

def detect_outliers(df, z_threshold=5):
    """
    Detect price outliers based on Z-score of 'close' within each asset group.
    Returns DataFrame of outlier rows with a 'z_score' column.
    """
    df = df.copy()
    df['z_score'] = df.groupby('asset_id')['close'].transform(zscore)
    return df[abs(df['z_score']) > z_threshold]
