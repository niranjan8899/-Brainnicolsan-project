import streamlit as st
import pandas as pd
import plotly.express as px
import duckdb
import os
from utils.data_cleaner import detect_missing_data, detect_outliers

# ---------- Data Loading ----------
@st.cache_data
def load_metadata():
    query = "SELECT * FROM 'data/asset_metadata.parquet'"
    return duckdb.query(query).to_df()

@st.cache_data
def load_price_data():
    query = "SELECT asset_id, date, close FROM 'data/price_data.parquet'"
    return duckdb.query(query).to_df()

@st.cache_data
def load_price_data_for_asset(asset_id: str):
    query = f"""
        SELECT asset_id, date, close FROM 'data/price_data.parquet'
        WHERE asset_id = '{asset_id}'
    """
    return duckdb.query(query).to_df()

# ----------- UI -----------
st.set_page_config(page_title="🧹 Data Cleaning Tool", layout="wide")
st.title("🧹 Data Cleaning & Validation Tool")

price_data = load_price_data()

st.subheader("📌 Step 1: Detect Missing Data")
missing_assets = detect_missing_data(price_data)
st.write(f"Found {len(missing_assets)} assets with gaps > 6 days")
st.dataframe(pd.DataFrame(missing_assets, columns=["Asset ID with Missing Data"]))

st.subheader("📌 Step 2: Detect Outliers")
outlier_df = detect_outliers(price_data)

if not outlier_df.empty:
    st.write(f"Found {len(outlier_df)} potential outliers")
    st.dataframe(outlier_df[["asset_id", "date", "close", "z_score"]].sort_values("z_score", ascending=False))

    selected_asset = st.selectbox("Select an asset to view chart", outlier_df["asset_id"].unique())

    chart_df = load_price_data_for_asset(selected_asset)
    fig = px.line(chart_df, x="date", y="close", title=f"Price Chart for {selected_asset} (Outliers visible)")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.success("✅ No extreme outliers detected.")

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
