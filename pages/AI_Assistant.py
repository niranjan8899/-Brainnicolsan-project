import streamlit as st
import pandas as pd
import numpy as np
from utils.ai_agent import get_ai_response

# ----------- Load Data -----------
@st.cache_data
def load_minimal_price_data():
    # Load the CSV file instead of Parquet
    df = pd.read_csv("data/asset_Economic.FRED.DGS30.csv")
    # Ensure the columns match the required format: "asset_id", "date", "close", "log_return"
    df['date'] = pd.to_datetime(df['date'])  # Ensure 'date' column is in datetime format
    df['log_return'] = np.log(df['close'] / df['close'].shift(1))  # Calculate log returns
    return df[['asset_id', 'date', 'close', 'log_return']]  # Return only required columns

@st.cache_data
def load_metadata():
    try:
        return pd.read_csv("data/asset_metadata.csv")
    except FileNotFoundError:
        st.error("The file 'asset_metadata.csv' is missing. Please ensure it exists in the 'data' folder.")
        return pd.DataFrame()  # Return an empty DataFrame if the file is missing

@st.cache_data
def load_nav_data():
    try:
        return pd.read_csv("data/portfolio_navs.csv")
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
