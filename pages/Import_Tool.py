# 2_Import_Tool.py

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# --------- Setup ---------
st.set_page_config(page_title="💹 Colorful Portfolio Import Tool", layout="wide")
st.markdown("<h1 style='text-align: center; color: #5D3FD3;'>🎨 Portfolio Import & Visualizer Tool</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 18px;'>Import financial data, validate it, and visualize performance over time with flair.</p>", unsafe_allow_html=True)

# --------- Data Series Definition Section ---------
st.markdown("## 📝 Data Series Definition")

with st.expander("Data File Configuration"):
    col1, col2 = st.columns(2)
    
    with col1:
        # Data File section
        st.markdown("### Data File")
        # Note: No file uploader here, since we are loading directly
        st.info("Loading file: asset_Economic.FRED.DGS30.csv")
        series_type = st.selectbox("Series_type", ["ETF","Economic","FUND", "features", "Index"], key="series_type")
        percentage_values = st.checkbox("Percentage Values", key="percentage_values")
        import_yield = st.checkbox("Import Yield", key="import_yield")
        series_name = st.text_input("Asset_id", key="asset_id")
        assigned_ticker = st.text_input("Assigned Ticker", key="assigned_ticker")
        description = st.text_area("Description", key="description")
    
    with col2:
        # Use as Asset Class section
        st.markdown("### Use as Asset Class")
        asset_class = st.checkbox("Asset Class", key="asset_class")
        asset_category = st.selectbox("Asset Category", ["None", "Equity", "Fixed Income", "Commodity", "Currency", "Other"], key="asset_category")

# --------- Upload and Processing Section ---------

try:
    # Load the file directly
    df = pd.read_csv("asset_Economic.FRED.DGS30.csv")

    # Standardize column names (case insensitive)
    df.columns = df.columns.str.lower().str.replace(' ', '_')
    
    # Expected columns based on your specification
    expected_columns = {
        'asset_id', 'date', 'open', 'high', 'low', 'close', 
        'volume', 'open_interest', 'daily_pct_change', 'log_return'
    }
    
    # Validate columns
    missing_columns = expected_columns - set(df.columns)
    if missing_columns:
        st.error(f"❌ Missing required columns: {missing_columns}")
    else:
        st.success("✅ File structure validated successfully!")
        
        # Convert and sort dates
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date")
        
        # Display data preview
        st.markdown("### 🔍 Preview of Uploaded Data")
        st.dataframe(df.head(), use_container_width=True)

        # Summary statistics
        st.markdown("### 📊 Summary Statistics")
        st.dataframe(df.describe(include='all'), use_container_width=True)

        # Price visualization
        st.markdown("### 📈 Price Chart (OHLC)")
        asset_display_name = series_name if series_name else df["asset_id"].iloc[0]
        
        # OHLC chart
        fig_ohlc = px.line(df, x="date", y=["open", "high", "low", "close"], 
                         title=f"📊 OHLC Prices for {asset_display_name}",
                         labels={"date": "Date", "value": "Price"},
                         template="plotly_dark")
        st.plotly_chart(fig_ohlc, use_container_width=True)

        # Volume chart if available
        if 'volume' in df.columns:
            st.markdown("### 📊 Trading Volume")
            fig_volume = px.bar(df, x="date", y="volume", 
                               title=f"📊 Trading Volume for {asset_display_name}",
                               labels={"date": "Date", "volume": "Volume"},
                               template="plotly_dark")
            st.plotly_chart(fig_volume, use_container_width=True)

        # Return series visualization
        st.markdown("### 🔁 Return Series")
        return_options = []
        if 'daily_pct_change' in df.columns:
            return_options.append(('Daily Percentage', 'daily_pct_change'))
        if 'log_return' in df.columns:
            return_options.append(('Log Return', 'log_return'))
        
        if return_options:
            selected_return = st.selectbox("Choose return series to visualize", 
                                         [opt[0] for opt in return_options])
            return_col = [opt[1] for opt in return_options if opt[0] == selected_return][0]
            
            fig_returns = px.line(df, x="date", y=return_col, 
                                title=f"📉 {selected_return} over Time",
                                labels={"date": "Date", return_col: "Return"},
                                template="plotly_white")
            st.plotly_chart(fig_returns, use_container_width=True)
        else:
            st.warning("No return series found in the data (daily_pct_change or log_return)")

except Exception as e:
    st.error(f"❌ Error processing file: {str(e)}")

# --------- Action Buttons ---------
st.markdown("---")
col1, col2 = st.columns(2)
with col1:
    if st.button("💾 Save Configuration", key="save_btn"):
        if 'df' in locals():
            st.success("Configuration and data saved successfully!")
        else:
            st.warning("Please upload a valid file first")
with col2:
    if st.button("❌ Cancel", key="cancel_btn"):
        st.warning("Operation cancelled")

# --------- Footer ---------
st.markdown("---")
st.markdown(
    "<div style='text-align: center; font-size: 14px; color: gray;'>"
    "Tool developed for colorful and clear financial data validation. "
    "Supports: OHLC prices, volume, percentage returns, log returns. More updates coming soon."
    "</div>",
    unsafe_allow_html=True
)
