# 7_AI_Assistant.py

import streamlit as st
import pandas as pd
import pyarrow.parquet as pq
from utils.ai_agent import get_ai_response

# ----------- Load Data -----------
@st.cache_data
def load_minimal_price_data():
    table = pq.read_table("data/price_data.parquet", columns=["asset_id", "date", "close", "log_return"])
    return table.to_pandas()

@st.cache_data
def load_metadata():
    return pd.read_parquet("data/asset_metadata.parquet")

@st.cache_data
def load_nav_data():
    try:
        return pd.read_parquet("data/portfolio_navs.parquet")
    except FileNotFoundError:
        return pd.DataFrame()

# ----------- UI -----------
st.set_page_config(page_title="🧠 AI Assistant", layout="wide")
st.title("🧠 Agentic AI Portfolio Assistant")

price_data = load_minimal_price_data()
metadata = load_metadata()
portfolio_navs = load_nav_data()

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

for role, msg in st.session_state.chat_history:
    with st.chat_message(role):
        st.markdown(msg)

query = st.chat_input("Ask me anything about your portfolio...")
if query:
    st.session_state.chat_history.append(("user", query))
    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = get_ai_response(query, metadata, price_data, portfolio_navs)
            st.markdown(response)
            st.session_state.chat_history.append(("assistant", response))
