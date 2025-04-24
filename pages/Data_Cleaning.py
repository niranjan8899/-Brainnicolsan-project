import streamlit as st
import pandas as pd
import plotly.express as px
import pyarrow.parquet as pq
from utils.data_cleaner import detect_missing_data, detect_outliers
import gdown
import os

# ------------------ Google Drive Setup ------------------
PRICE_DATA_DRIVE_URL = "https://drive.google.com/uc?id=/1I1zViTWNsIbTwfFMoqNCevqrADk12YSV"

# ------------------ Download from Google Drive ------------------
def download_from_drive(gdrive_url, output_path):
    if not os.path.exists(output_path):
        gdown.download(gdrive_url, output_path, quiet=False)

# ------------------ Load Only Needed Data ------------------
@st.cache_data
def load_minimal_price_data():
    download_from_drive(PRICE_DATA_DRIVE_URL, "price_data.parquet")
    table = pq.read_table("price_data.parquet", columns=["asset_id", "date", "close"])
    df = table.to_pandas()
    return df

@st.cache_data
def load_asset_price_data(asset_id):
    df = load_minimal_price_data()
    return df[df["asset_id"] == asset_id]

# ------------------ UI ------------------
st.set_page_config(page_title="🧹 Data Cleaning Tool", layout="wide")
st.title("🧹 Data Cleaning & Validation Tool")

price_data = load_minimal_price_data()

# ----------- Step 1: Detect Missing Data -----------
st.subheader("📌 Step 1: Detect Missing Data")
missing_assets = detect_missing_data(price_data)
st.write(f"Found {len(missing_assets)} assets with gaps > 6 days")
st.dataframe(pd.DataFrame(missing_assets, columns=["Asset ID with Missing Data"]))

# ----------- Step 2: Detect Outliers -----------
st.subheader("📌 Step 2: Detect Outliers")
outlier_df = detect_outliers(price_data)

if not outlier_df.empty:
    st.write(f"Found {len(outlier_df)} potential outliers")
    st.dataframe(outlier_df[["asset_id", "date", "close", "z_score"]].sort_values("z_score", ascending=False))

    selected_asset = st.selectbox("Select an asset to view chart", outlier_df["asset_id"].unique())

    chart_df = load_asset_price_data(selected_asset)
    fig = px.line(chart_df, x="date", y="close", title=f"Price Chart for {selected_asset} (Outliers visible)")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.success("✅ No extreme outliers detected.")

# ----------- Simulate Cleaning -----------
st.markdown("---")

if st.button("🚀 Simulate Cleaning (Tag Outliers)"):
    cleaned = price_data.copy()
    cleaned["has_error"] = False
    cleaned["error_type"] = None

    outlier_index = outlier_df.index
    cleaned.loc[outlier_index, "has_error"] = True
    cleaned.loc[outlier_index, "error_type"] = "outlier_zscore"

    st.success("Outliers tagged in memory (not saved).")
    st.dataframe(cleaned[cleaned["has_error"] == True][["asset_id", "date", "close", "error_type"]])
