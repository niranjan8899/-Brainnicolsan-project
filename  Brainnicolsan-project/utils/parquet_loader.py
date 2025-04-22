# utils/parquet_loader.py

import pandas as pd
from pathlib import Path

data_folder = Path("data")

# ----------- Loaders -----------
def load_metadata():
    return pd.read_parquet(data_folder / "asset_metadata.parquet")

def load_price_data():
    return pd.read_parquet(data_folder / "price_data.parquet")

# ----------- Savers -----------
def save_metadata(df):
    df.to_parquet(data_folder / "asset_metadata.parquet", index=False)

def save_price_data(df):
    df.to_parquet(data_folder / "price_data.parquet", index=False)
