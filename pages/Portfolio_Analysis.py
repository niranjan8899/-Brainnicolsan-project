# Portfolio Analysis Tool


import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import duckdb
import json
from utils.backtest_engine import prepare_data, compute_portfolio_nav
from utils.analysis_tools import compare_multiple_portfolios

# ----------- DuckDB Configuration -----------

DUCKDB_PATH = "data/portfolio.db"

def get_duckdb_connection():
    return duckdb.connect(database=DUCKDB_PATH)

def initialize_db():
    con = get_duckdb_connection()
    con.execute("""
        CREATE TABLE IF NOT EXISTS saved_portfolios (
            name TEXT PRIMARY KEY,
            assets TEXT, -- JSON list
            weights TEXT -- JSON list
        )
    """)
    con.close()

initialize_db()

# ----------- Load Metadata -----------

@st.cache_data
def load_metadata():
    con = get_duckdb_connection()
    df = con.execute("SELECT * FROM 'data/asset_metadata.parquet'").df()
    con.close()
    return df

# ----------- Load Price Data -----------

@st.cache_data
def load_filtered_price_data(selected_assets, start_date, end_date):
    con = get_duckdb_connection()
    asset_list = ','.join(f"'{a}'" for a in selected_assets)
    
    query = f"""
        SELECT * FROM 'data/price_data.parquet'
        WHERE asset_id IN ({asset_list})
        AND date BETWEEN '{start_date}' AND '{end_date}'
    """
    df = con.execute(query).df()
    con.close()
    return df

# ----------- Save & Load Portfolios -----------

def save_portfolio(name, assets, weights):
    con = get_duckdb_connection()
    con.execute("INSERT OR REPLACE INTO saved_portfolios VALUES (?, ?, ?)",
                (name, json.dumps(assets), json.dumps(weights)))
    con.close()

def load_saved_portfolios():
    con = get_duckdb_connection()
    rows = con.execute("SELECT * FROM saved_portfolios").fetchall()
    con.close()
    return {name: (json.loads(a), json.loads(w)) for name, a, w in rows}

# ----------- UI -----------

st.set_page_config(page_title="📊 Portfolio Analysis Tool", layout="wide")
st.title("📊 Portfolio Comparison & Analysis Tool")

metadata = load_metadata()
asset_options = metadata['asset_id'].unique()

# Load saved portfolios
saved = load_saved_portfolios()

st.sidebar.header("💾 Saved Portfolios")
selected_saved_names = st.sidebar.multiselect("Load saved portfolios", options=list(saved.keys()))
portfolios = []

# Load portfolios from selection
for name in selected_saved_names:
    assets, weights = saved[name]
    portfolios.append((assets, weights))

st.subheader("🧺 Define New Portfolios")
num_new = st.number_input("Number of new portfolios to create", min_value=0, max_value=5, value=0)

for i in range(num_new):
    with st.expander(f"📦 New Portfolio {i+1}"):
        name = st.text_input(f"Portfolio Name {i+1}", key=f"name_{i}")
        assets = st.multiselect(f"Select assets", options=asset_options, key=f"assets_{i}")
        weights = []

        if assets:
            st.write("Assign weights (must total 100%)")
            for a in assets:
                w = st.number_input(f"{a} weight (%)", key=f"weight_{i}_{a}", min_value=0.0, max_value=100.0, value=round(100/len(assets), 2))
                weights.append(w)

            if sum(weights) != 100:
                st.error("❌ Weights must total 100%")
            elif st.button(f"💾 Save Portfolio {i+1}", key=f"save_btn_{i}"):
                if name.strip() == "":
                    st.warning("Please provide a portfolio name before saving.")
                else:
                    save_portfolio(name, assets, weights)
                    st.success(f"✅ Saved as '{name}'")
                    st.rerun()
            else:
                portfolios.append((assets, weights))

# ----------- Date Range -----------

if portfolios:
    st.subheader("📅 Select Time Period")
    start_date = st.date_input("Start Date", value=pd.to_datetime("2015-01-01").date())
    end_date = st.date_input("End Date", value=pd.to_datetime("2023-12-31").date(), min_value=start_date)

    if st.button("🚀 Compare Portfolios"):
        all_assets = list(set([a for portfolio, _ in portfolios for a in portfolio]))
        price_data = load_filtered_price_data(all_assets, start_date, end_date)

        if price_data.empty:
            st.warning("No price data available.")
        else:
            navs = {}
            for i, (assets, weights) in enumerate(portfolios):
                df = prepare_data(price_data, assets, start_date, end_date)
                nav = compute_portfolio_nav(df, weights)
                navs[f"Portfolio {i+1}"] = nav

            # NAV Chart
            nav_df = pd.DataFrame(navs)
            st.subheader("📈 NAV Comparison")
            fig = px.line(nav_df, x=nav_df.index, y=nav_df.columns, labels={"value": "NAV", "index": "Date"})
            st.plotly_chart(fig, use_container_width=True)

            # Metrics Table
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
