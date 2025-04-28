import streamlit as st
import pandas as pd
import plotly.express as px
from sklearn.linear_model import LinearRegression
import numpy as np

# ------------------ Load Asset IDs ------------------
@st.cache_data
def load_asset_ids():
    df = pd.read_csv("asset_Economic.FRED.DGS30.csv", parse_dates=["date"])
    return sorted(df["asset_id"].unique())

# ------------------ Load Data for Selected Asset ------------------
@st.cache_data
def load_asset_data(asset_id):
    df = pd.read_csv("asset_Economic.FRED.DGS30.csv", parse_dates=["date"])
    return df[df["asset_id"] == asset_id].dropna(subset=["log_return"])

# ------------------ Streamlit UI ------------------
st.set_page_config(page_title="🧬 Historical Simulation Tool", layout="wide")
st.title("🧬 Asset Historical Simulation Tool")

asset_ids = load_asset_ids()

col1, col2 = st.columns(2)
with col1:
    target_asset = st.selectbox("Select Target Asset", asset_ids)
with col2:
    proxy_asset = st.selectbox("Select Proxy Asset", asset_ids)

if target_asset and proxy_asset and target_asset != proxy_asset:
    target_df = load_asset_data(target_asset)
    proxy_df = load_asset_data(proxy_asset)

    # Merge data for comparison
    merged = pd.merge(
        target_df[["date", "log_return", "close"]],
        proxy_df[["date", "log_return", "close"]],
        on="date",
        suffixes=("_target", "_proxy")
    )

    # Train regression model
    X = merged[["log_return_proxy"]].rename(columns={"log_return_proxy": "log_return"})
    y = merged["log_return_target"]
    model = LinearRegression().fit(X, y)
    merged["fitted"] = model.predict(X)
    r_squared = model.score(X, y)

    # --- Price History Plot ---
    st.subheader("⏳ Price Evolution Over Time")
    fig_time = px.line(
        merged,
        x="date",
        y=["close_target", "close_proxy"],
        labels={"value": "Price", "variable": "Asset"},
        title="Actual Price History Comparison"
    )
    st.plotly_chart(fig_time, use_container_width=True)

    # --- Return Analysis ---
    st.subheader("📈 Return Relationship Analysis")
    st.write(f"**R² Score:** {r_squared:.4f}")

    col1, col2 = st.columns(2)
    with col1:
        fig_scatter = px.scatter(
            merged,
            x="log_return_proxy",
            y="log_return_target",
            trendline="ols",
            title="Daily Log Returns Relationship",
            labels={
                "log_return_proxy": "Proxy Returns",
                "log_return_target": "Target Returns"
            }
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

    with col2:
        merged['rolling_corr'] = merged['log_return_target'].rolling(30).corr(merged['log_return_proxy'])
        fig_corr = px.line(
            merged,
            x="date",
            y="rolling_corr",
            title="30-Day Rolling Correlation",
            labels={"rolling_corr": "Correlation"}
        )
        st.plotly_chart(fig_corr, use_container_width=True)

    # --- Simulation ---
    st.subheader("🧪 Historical Simulation")
    extension_range = st.slider("Days to simulate before target starts", 30, 500, 180)

    earliest_target_date = target_df["date"].min()
    proxy_history = proxy_df[proxy_df["date"] < earliest_target_date].sort_values("date").tail(extension_range)

    if not proxy_history.empty:
        proxy_history = proxy_history.copy()
        prediction_input = proxy_history[["log_return"]].rename(columns={"log_return": "log_return_proxy"})
        proxy_history["log_return_target_sim"] = model.predict(prediction_input.rename(columns={"log_return_proxy": "log_return"}))

        base_price = target_df["close"].iloc[0]
        proxy_history["simulated_price"] = base_price * np.exp(proxy_history["log_return_target_sim"].cumsum())
        proxy_history["asset_id"] = target_asset
        proxy_history["is_simulated"] = True

        combined = pd.concat([
            proxy_history[["date", "simulated_price", "is_simulated"]],
            target_df[["date", "close"]].rename(columns={"close": "simulated_price"}).assign(is_simulated=False)
        ]).sort_values("date")

        st.success(f"✅ Simulated {len(proxy_history)} days of data before {earliest_target_date.date()}.")

        fig_combined = px.line(
            combined,
            x="date",
            y="simulated_price",
            color="is_simulated",
            labels={"simulated_price": "Price", "is_simulated": "Simulated"},
            title="Combined Actual + Simulated Price History",
            color_discrete_map={True: "orange", False: "blue"}
        )
        st.plotly_chart(fig_combined, use_container_width=True)

        fig_returns = px.line(
            proxy_history,
            x="date",
            y="log_return_target_sim",
            title="Simulated Daily Returns Over Time",
            labels={"log_return_target_sim": "Log Return"}
        )
        st.plotly_chart(fig_returns, use_container_width=True)
    else:
        st.warning("❌ Not enough proxy data before target's start date.")
