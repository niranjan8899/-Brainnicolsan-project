import streamlit as st
import pandas as pd
import plotly.express as px
from st_aggrid import AgGrid, GridOptionsBuilder

# ---------- Load Data ----------
@st.cache_data
def load_metadata():
    return pd.read_csv("data/asset_metadata.csv")  # Changed to CSV file

@st.cache_data
def load_price_data_for_asset(asset_id: str):
    df = pd.read_csv("data/price_data.csv")  # Changed to CSV file
    return df[df['asset_id'] == asset_id].copy()

# ---------- Page Setup ----------
st.set_page_config(page_title="📊 Market Screener", layout="wide")
st.markdown("""
    <style>
        .main {background-color: #000000;}
        .block-container {padding-top: 1rem; background-color: #000000;}
        h1, h2, h3, h4 {
            color: #ffffff;
        }
        .stRadio > div {flex-direction: row;}
        .stSelectbox label, .stTextInput label {
            font-weight: bold;
            color: #ffffff;
        }
        .stTextInput input, .stSelectbox select {
            background-color: #333333;
            color: white;
        }
        .stRadio label {
            color: white;
        }
        .ag-theme-streamlit {
            border-radius: 8px;
            border: 1px solid #444;
            background-color: #111;
        }
        .ag-header {
            background-color: #222 !important;
            color: white !important;
        }
        .ag-row {
            background-color: #111 !important;
            color: white !important;
        }
        .ag-cell {
            border-color: #444 !important;
        }
        .stButton button {
            background-color: #333;
            color: white;
            border: 1px solid #555;
        }
        .stButton button:hover {
            background-color: #444;
        }
        .stExpander {
            background-color: #111;
            border: 1px solid #444;
            border-radius: 8px;
        }
        .stExpander label {
            color: white !important;
        }
    </style>
""", unsafe_allow_html=True)

st.title("📊 Market Screener and Search Tool")

# ---------- Load Metadata ----------
metadata = load_metadata()

# ---------- Search Filters ----------
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

# ---------- Apply Filters ----------
filtered = metadata.copy()
if asset_id_input:
    filtered = filtered[filtered["asset_id"].str.contains(asset_id_input, case=False, na=False)]
if code_input:
    filtered = filtered[filtered["code"].str.contains(code_input, case=False, na=False)]
if name_input:
    filtered = filtered[filtered["name"].str.contains(name_input, case=False, na=False)]
if description_input:
    filtered = filtered[filtered["description"].str.contains(description_input, case=False, na=False)]

# ---------- Dropdown Filters ----------
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

# ---------- Display Asset Table ----------
st.markdown("### 🧾 Asset Results")
gb = GridOptionsBuilder.from_dataframe(filtered)
gb.configure_pagination()
gb.configure_default_column(groupable=True, filterable=True, editable=False)
gb.configure_selection('single')
grid_options = gb.build()

grid_response = AgGrid(
    filtered,
    gridOptions=grid_options,
    height=400,
    enable_enterprise_modules=False,
    theme='streamlit',
    custom_css={
        ".ag-header-cell-label": {"color": "white"},
        ".ag-cell": {"color": "white"}
    }
)

# ---------- Summary Charts ----------
st.markdown("### 📊 Summary Visualizations")

# Update Plotly template to dark
plotly_template = "plotly_dark"

# Pie Chart for Asset Type Distribution
if not filtered.empty and "asset_type" in filtered.columns:
    pie_fig = px.pie(
        filtered,
        names="asset_type",
        title="Asset Type Distribution",
        hole=0.4,
        template=plotly_template
    )
    st.plotly_chart(pie_fig, use_container_width=True)

# Bar Chart for Exchange Distribution
if "exchange" in filtered.columns:
    exchange_counts = filtered["exchange"].value_counts().reset_index()
    exchange_counts.columns = ["Exchange", "Count"]

    exchange_bar = px.bar(
        exchange_counts,
        x="Exchange",
        y="Count",
        title="Assets by Exchange",
        labels={"Exchange": "Exchange", "Count": "Number of Assets"},
        template=plotly_template
    )
    st.plotly_chart(exchange_bar, use_container_width=True)

# ---------- Price Chart ----------
selected = grid_response['selected_rows']
if selected:
    asset_id = selected[0]["asset_id"]
    st.markdown(f"### 📈 Price & Return Chart for `{asset_id}`")

    df = load_price_data_for_asset(asset_id)
    if df.empty:
        st.warning("No price data available.")
    else:
        df['cumulative_return'] = (1 + df['daily_pct_change'] / 100).cumprod()

        chart_mode = st.radio("View Mode:", ['Price', 'Cumulative Return'], horizontal=True)
        y_axis = 'close' if chart_mode == 'Price' else 'cumulative_return'

        time_range = st.radio("Select Time Range:", ['1Y', '5Y', '10Y', 'All'], horizontal=True)
        if time_range != 'All':
            years = int(time_range.replace("Y", ""))
            df = df[df['date'] >= (pd.to_datetime(df['date'].max()) - pd.DateOffset(years=years))]

        fig = px.line(
            df,
            x='date',
            y=y_axis,
            labels={"date": "Date", y_axis: "Value"},
            title=f"{chart_mode} over Time",
            template=plotly_template
        )
        fig.update_traces(line=dict(color="#2a9d8f"))
        st.plotly_chart(fig, use_container_width=True)
