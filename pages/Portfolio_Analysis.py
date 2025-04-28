import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from utils.backtest_engine import prepare_data, compute_portfolio_nav, compute_metrics
from utils.analysis_tools import compare_multiple_portfolios

# ----------- Load Metadata -----------
@st.cache_data
def load_metadata():
    return pd.read_csv("data/asset_Economic.FRED.DGS30.csv")

# ----------- Load Filtered Price Data -----------
@st.cache_data
def load_filtered_price_data(selected_assets, start_date, end_date):
    # Use asset_Economic.FRED.DGS30.csv as the new data file
    df = pd.read_csv("data/asset_Economic.FRED.DGS30.csv")  # Updated file path
    # Ensure date column is datetime64[ns]
    df['date'] = pd.to_datetime(df['date'])
    # Convert input dates to pandas Timestamp for proper comparison
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    df = df[df["asset_id"].isin(selected_assets) & 
            (df["date"] >= start_date) & 
            (df["date"] <= end_date)]
    return df

# ----------- UI -----------
st.set_page_config(page_title="📊 Portfolio Analysis Tool", layout="wide")
st.title("📊 Portfolio Comparison & Analysis Tool")

metadata = load_metadata()
asset_options = metadata['asset_id'].unique()

st.subheader("🧺 Define Portfolios")
num_portfolios = st.number_input("Number of portfolios to compare", min_value=2, max_value=5, value=2)
portfolios = []

for i in range(num_portfolios):
    with st.expander(f"📦 Portfolio {i+1}"):
        assets = st.multiselect(f"Select assets for Portfolio {i+1}", options=asset_options, key=f"assets_{i}")
        weights = []
        if assets:
            st.write("Assign weights (must total 100%)")
            for a in assets:
                w = st.number_input(f"{a} weight (%)", key=f"weight_{i}_{a}", min_value=0.0, max_value=100.0, value=round(100/len(assets), 2))
                weights.append(w)
            if sum(weights) != 100:
                st.error(f"❌ Weights for Portfolio {i+1} must total 100%.")
            else:
                portfolios.append((assets, weights))

# Only show date pickers once at least one valid portfolio is defined
if portfolios:
    st.subheader("📅 Select Time Period")
    # Set static global min/max date for now
    start_date = st.date_input("Start Date", value=pd.to_datetime("2015-01-01").date())
    end_date = st.date_input("End Date", value=pd.to_datetime("2023-12-31").date(), min_value=start_date)

    if st.button("🚀 Compare Portfolios"):
        # Collect all unique assets across all portfolios
        all_assets = list(set([a for portfolio, _ in portfolios for a in portfolio]))

        # Load only required price data
        price_data = load_filtered_price_data(all_assets, start_date, end_date)
        if price_data.empty:
            st.warning("No price data available for selected portfolios and period.")
        else:
            navs = {}
            for i, (assets, weights) in enumerate(portfolios):
                # Convert dates to datetime64[ns] before passing to prepare_data
                start_dt = pd.to_datetime(start_date)
                end_dt = pd.to_datetime(end_date)
                df = prepare_data(price_data, assets, start_dt, end_dt)
                nav = compute_portfolio_nav(df, weights)
                navs[f"Portfolio {i+1}"] = nav

            # NAV Chart
            nav_df = pd.DataFrame(navs)
            st.subheader("📈 NAV Comparison")
            fig = px.line(nav_df, x=nav_df.index, y=nav_df.columns, labels={"value": "NAV", "index": "Date"})
            st.plotly_chart(fig, use_container_width=True)

            # Metrics Table (Advanced)
            metrics_df = compare_multiple_portfolios(navs)
            st.subheader("📊 Performance Metrics")
            st.dataframe(metrics_df)

            # Pie Charts
            st.subheader("📌 Portfolio Allocations")
            cols = st.columns(len(portfolios))
            for i, (assets, weights) in enumerate(portfolios):
                with cols[i % len(cols)]:
                    fig = px.pie(names=assets, values=weights, title=f"Portfolio {i+1} Allocation")
                    st.plotly_chart(fig, use_container_width=True)
