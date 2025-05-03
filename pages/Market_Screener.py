import streamlit as st
import pandas as pd
import plotly.express as px
import duckdb
from st_aggrid import AgGrid, GridOptionsBuilder

# ---------- Data Loading ----------
@st.cache_data
def load_metadata():
    query = "SELECT * FROM 'data/asset_metadata.parquet'"
    return duckdb.query(query).to_df()

@st.cache_data
def load_price_data_for_asset(asset_id: str):
    query = f"""
        SELECT * FROM 'data/price_data.parquet'
        WHERE asset_id = '{asset_id}'
    """
    return duckdb.query(query).to_df()

# ---------- Persistent Save ----------
def save_selected_assets(selected_assets):
    con = duckdb.connect(database='data/selected_assets.duckdb')  # Save in a DuckDB file
    con.execute("CREATE TABLE IF NOT EXISTS selected_assets (asset_id TEXT)")
    con.execute("DELETE FROM selected_assets")
    for asset_id in selected_assets:
        con.execute("INSERT INTO selected_assets VALUES (?)", (asset_id,))
    con.close()

def load_selected_assets():
    con = duckdb.connect(database='data/selected_assets.duckdb')  # Same file for loading
    try:
        df = con.execute("SELECT asset_id FROM selected_assets").fetchdf()
        return df['asset_id'].tolist()
    except:
        return []
    finally:
        con.close()


# ---------- Main App ----------
def main():
    st.set_page_config(page_title="📊 Market Screener", layout="wide")
    st.title("📊 Market Screener and Search Tool")

    metadata = load_metadata()

    # Search Filters
    with st.expander("🔍 Search Filters", expanded=True):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            asset_id_input = st.text_input("Asset ID")
        with col2:
            code_input = st.text_input("Code")
        with col3:
            name_input = st.text_input("Name")
        with col4:
            description_input = st.text_input("Description")
        if st.button("Clear All"):
            asset_id_input = code_input = name_input = description_input = ""

    filtered = metadata.copy()
    if asset_id_input:
        filtered = filtered[filtered["asset_id"].str.contains(asset_id_input, case=False, na=False)]
    if code_input:
        filtered = filtered[filtered["code"].str.contains(code_input, case=False, na=False)]
    if name_input:
        filtered = filtered[filtered["name"].str.contains(name_input, case=False, na=False)]
    if description_input:
        filtered = filtered[filtered["description"].str.contains(description_input, case=False, na=False)]

    # Advanced Filters
    with st.expander("⚙️ Advanced Filters"):
        col1, col2, col3 = st.columns(3)
        asset_types = [""] + sorted(metadata["asset_type"].dropna().unique().tolist())
        exchanges = [""] + sorted(metadata["exchange"].dropna().unique().tolist())
        categories = [""] + sorted(metadata["category"].dropna().unique().tolist())

        with col1:
            selected_asset_type = st.selectbox("Asset Type", asset_types)
        with col2:
            selected_exchange = st.selectbox("Exchange", exchanges)
        with col3:
            selected_category = st.selectbox("Category", categories)

        if selected_asset_type:
            filtered = filtered[filtered["asset_type"] == selected_asset_type]
        if selected_exchange:
            filtered = filtered[filtered["exchange"] == selected_exchange]
        if selected_category:
            filtered = filtered[filtered["category"] == selected_category]

    # Display Table
    st.markdown("### 🧾 Asset Results")
    gb = GridOptionsBuilder.from_dataframe(filtered)
    gb.configure_pagination()
    gb.configure_default_column(groupable=True, filterable=True, editable=False)
    gb.configure_selection('multiple')
    grid_options = gb.build()

    grid_response = AgGrid(
        filtered,
        gridOptions=grid_options,
        height=400,
        enable_enterprise_modules=False,
        theme='streamlit'
    )

    selected_rows = grid_response.get('selected_rows') or []
    selected_asset_ids = [row['asset_id'] for row in selected_rows]

    if selected_asset_ids:
        save_selected_assets(selected_asset_ids)

    # Summary Charts
    st.markdown("### 📊 Summary Visualizations")

    if not filtered.empty and "asset_type" in filtered.columns:
        pie_fig = px.pie(
            filtered,
            names="asset_type",
            title="Asset Type Distribution",
            hole=0.4,
            template="plotly_white"
        )
        st.plotly_chart(pie_fig, use_container_width=True)

    if "exchange" in filtered.columns:
        exchange_counts = filtered["exchange"].value_counts().reset_index()
        exchange_counts.columns = ["Exchange", "Count"]
        exchange_bar = px.bar(
            exchange_counts,
            x="Exchange",
            y="Count",
            title="Assets by Exchange",
            labels={"Exchange": "Exchange", "Count": "Number of Assets"},
            template="plotly_white"
        )
        st.plotly_chart(exchange_bar, use_container_width=True)

    # Price Charts
    if selected_asset_ids:
        st.markdown("### 📈 Price & Return Chart for Selected Assets")
        chart_mode = st.radio("View Mode:", ['Price', 'Cumulative Return'], horizontal=True)
        y_axis = 'close' if chart_mode == 'Price' else 'cumulative_return'

        time_range = st.radio("Select Time Range:", ['1Y', '5Y', '10Y', 'All'], horizontal=True)
        combined_df = pd.DataFrame()

        for asset_id in selected_asset_ids:
            df = load_price_data_for_asset(asset_id)
            if df.empty:
                continue
            df['cumulative_return'] = (1 + df['daily_pct_change'] / 100).cumprod()
            df['asset_id'] = asset_id

            if time_range != 'All':
                try:
                    df['date'] = pd.to_datetime(df['date'])
                    cutoff = {
                        '1Y': pd.Timestamp.now() - pd.DateOffset(years=1),
                        '5Y': pd.Timestamp.now() - pd.DateOffset(years=5),
                        '10Y': pd.Timestamp.now() - pd.DateOffset(years=10),
                    }[time_range]
                    df = df[df['date'] >= cutoff]
                except:
                    pass

            combined_df = pd.concat([combined_df, df], ignore_index=True)

        if not combined_df.empty:
            chart = px.line(
                combined_df,
                x='date',
                y=y_axis,
                color='asset_id',
                title=f"{chart_mode} over Time",
                template="plotly_white"
            )
            st.plotly_chart(chart, use_container_width=True)

# ---------- Run ----------
if __name__ == "__main__":
    main()
