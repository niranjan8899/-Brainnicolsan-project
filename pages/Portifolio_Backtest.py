import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import pyarrow.parquet as pq
import requests
from io import BytesIO
from datetime import date

# ----------- Google Drive Utility -----------
def download_from_drive(drive_url):
    file_id = drive_url.split("/d/")[1].split("/")[0]
    download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
    response = requests.get(download_url)
    if response.status_code != 200:
        st.error("Failed to fetch file from Google Drive.")
        return None
    return BytesIO(response.content)

# Replace with your actual Google Drive share links
METADATA_LINK = "https://drive.google.com/file/d/1P5eTXhvmn-5mtVtqMJg3yuBhbWKclEPs/view?usp=sharing"
PRICEDATA_LINK = "https://drive.google.com/file/d/1I1zViTWNsIbTwfFMoqNCevqrADk12YSV/view?usp=sharing"

# ----------- Load Metadata -----------
@st.cache_data
def load_metadata():
    f = download_from_drive(METADATA_LINK)
    return pd.read_parquet(f) if f else pd.DataFrame()

# ----------- Load Filtered Price Data -----------
@st.cache_data
def load_filtered_price_data(selected_assets, start_date, end_date):
    f = download_from_drive(PRICEDATA_LINK)
    if not f:
        return pd.DataFrame()
    table = pq.read_table(f)
    df = table.to_pandas()
    df['date'] = pd.to_datetime(df['date'])
    return df[df["asset_id"].isin(selected_assets) & df["date"].between(pd.to_datetime(start_date), pd.to_datetime(end_date))]

# ----------- UI -----------
st.set_page_config(page_title="📈 Portfolio Backtesting Tool", layout="wide")
st.title("📈 Portfolio Backtesting Tool")

metadata = load_metadata()
if metadata.empty:
    st.warning("Metadata could not be loaded. Please check the Google Drive link.")
else:
    asset_options = metadata['asset_id'].unique()

    st.subheader("🧺 Define Portfolio")
    portfolio_assets = st.multiselect("Select assets for portfolio", options=asset_options)

    weights = []
    if portfolio_assets:
        st.write("Assign weights to selected assets (must total 100%)")
        for asset in portfolio_assets:
            w = st.number_input(f"Weight for {asset} (%)", min_value=0.0, max_value=100.0,
                                value=round(100/len(portfolio_assets), 2))
            weights.append(w)

        if sum(weights) != 100:
            st.error("❌ Weights must total 100%.")
        else:
            st.success("✅ Portfolio is valid. You can run the backtest.")

            st.subheader("📅 Select Backtest Period")
            start_date = st.date_input("Start Date", value=date(2015, 1, 1))
            end_date = st.date_input("End Date", value=date(2023, 12, 31), min_value=start_date)

            if st.button("🚀 Run Backtest"):
                price_data = load_filtered_price_data(portfolio_assets, start_date, end_date)

                if price_data.empty:
                    st.warning("No price data found for selected assets and period.")
                else:
                    filtered = price_data.copy()
                    pivot = filtered.pivot(index='date', columns='asset_id', values='close')
                    pivot = pivot.fillna(method='ffill').dropna()
                    returns = pivot.pct_change().dropna()

                    weight_array = np.array(weights) / 100
                    portfolio_returns = returns.dot(weight_array)
                    portfolio_nav = (1 + portfolio_returns).cumprod()

                    st.subheader("📊 Portfolio NAV Chart")
                    fig = px.line(x=portfolio_nav.index, y=portfolio_nav.values,
                                  labels={'x': 'Date', 'y': 'Portfolio NAV'})
                    st.plotly_chart(fig, use_container_width=True)

                    st.subheader("📈 Performance Metrics")
                    cagr = (portfolio_nav.iloc[-1] ** (1 / ((portfolio_nav.index[-1] - portfolio_nav.index[0]).days / 365.25))) - 1
                    max_dd = ((portfolio_nav / portfolio_nav.cummax()) - 1).min()
                    st.write(f"**CAGR:** {cagr:.2%}")
                    st.write(f"**Max Drawdown:** {max_dd:.2%}")
