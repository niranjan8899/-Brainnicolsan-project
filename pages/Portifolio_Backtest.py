import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from datetime import date

# ----------- Load Metadata -----------
@st.cache_data
def load_metadata():
    # Assuming metadata is simple: using asset name from the CSV itself
    return pd.DataFrame({
        'asset_id': ['Economic.FRED.DGS30']
    })

# ----------- Load Filtered Price Data -----------
@st.cache_data
def load_filtered_price_data(selected_assets, start_date, end_date):
    # Load directly from local CSV
    df = pd.read_csv("asset_Economic.FRED.DGS30.csv")
    df['date'] = pd.to_datetime(df['date'])

    return df[df["asset_id"].isin(selected_assets) & df["date"].between(pd.to_datetime(start_date), pd.to_datetime(end_date))]

# ----------- UI -----------
st.set_page_config(page_title="📈 Portfolio Backtesting Tool", layout="wide")
st.title("📈 Portfolio Backtesting Tool")

metadata = load_metadata()
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
