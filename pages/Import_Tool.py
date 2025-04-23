# 2_Import_Tool.py

import streamlit as st
import pandas as pd
import pyarrow.parquet as pq
import plotly.express as px
from datetime import datetime
import io

# --------- Setup ---------
st.set_page_config(page_title="💹 Colorful Portfolio Import Tool", layout="wide")
st.markdown("<h1 style='text-align: center; color: #5D3FD3;'>🎨 Portfolio Import & Visualizer Tool</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 18px;'>Import financial data, validate it, and visualize performance over time with flair.</p>", unsafe_allow_html=True)

# --------- Upload Section ---------
st.markdown("### 📁 Upload Your CSV or Parquet File")
uploaded_file = st.file_uploader("Drag and drop or browse file", type=["csv", "parquet"])

if uploaded_file:
    file_type = uploaded_file.name.split(".")[-1].lower()
    
    try:
        if file_type == "csv":
            df = pd.read_csv(uploaded_file)
        elif file_type == "parquet":
            # Use pyarrow to read large Parquet file efficiently
            table = pq.read_table(uploaded_file)
            df = table.to_pandas()
        else:
            st.error("❌ Unsupported file type.")
            st.stop()
    except Exception as e:
        st.error(f"❌ Error reading file: {e}")
        st.stop()

    st.success("✅ File uploaded successfully!")

    # --------- Validation ---------
    required_cols = {"asset_id", "date", "close"}
    missing_cols = required_cols - set(df.columns)

    if missing_cols:
        st.error(f"❌ Missing required columns: {missing_cols}")
    else:
        # Convert and sort date
        try:
            df["date"] = pd.to_datetime(df["date"])
        except Exception as e:
            st.error(f"❌ Date conversion error: {e}")
            st.stop()

        df = df.sort_values("date")

        # --------- Display Data ---------
        st.markdown("### 🔍 Preview of Uploaded Data")
        st.dataframe(df.head(), use_container_width=True)

        st.markdown("### 📊 Summary Statistics")
        st.dataframe(df.describe(include='all'), use_container_width=True)

        # --------- Plot Close Prices ---------
        st.markdown("### 📈 Asset Price Chart")
        asset_name = df["asset_id"].iloc[0]
        fig = px.line(
            df,
            x="date",
            y="close",
            title=f"📊 Closing Prices for {asset_name}",
            labels={"date": "Date", "close": "Closing Price"},
            template="plotly_dark",
            color_discrete_sequence=["#00CC96"]
        )
        st.plotly_chart(fig, use_container_width=True)

        # --------- Optional Return Chart ---------
        if "daily_pct_change" in df.columns or "log_return" in df.columns:
            st.markdown("### 🔁 Return Series Chart")
            return_col = "daily_pct_change" if "daily_pct_change" in df.columns else "log_return"
            fig2 = px.line(
                df,
                x="date",
                y=return_col,
                title=f"📉 {return_col} over Time",
                labels={"date": "Date", return_col: "Return"},
                template="plotly_white",
                color_discrete_sequence=["#EF553B"]
            )
            st.plotly_chart(fig2, use_container_width=True)

        # --------- Commit Button ---------
        st.markdown("---")
        if st.button("🚀 Commit Import (Simulated)"):
            st.balloons()
            st.success("✅ Data import simulated successfully. Ready for backend integration!")

# --------- Footer ---------
st.markdown("---")
st.markdown(
    "<div style='text-align: center; font-size: 14px; color: gray;'>"
    "Tool developed for colorful and clear financial data validation. "
    "Supports: Close prices, % returns, log returns. More updates coming soon."
    "</div>",
    unsafe_allow_html=True
)
