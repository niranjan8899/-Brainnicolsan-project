# app.py
import warnings
warnings.filterwarnings("ignore", message="coroutine 'expire_cache' was never awaited")
import streamlit as st

st.set_page_config(page_title="Portfolio Analysis Tool", layout="wide")
st.title("📁 Portfolio Backtesting & Analysis App")

st.markdown("""
Welcome to your personal financial research toolkit.

Navigate using the sidebar to:
- 📊 Use the Market Screener
- 📥 Upload New Data

More tools will be added in future phases!
""")
