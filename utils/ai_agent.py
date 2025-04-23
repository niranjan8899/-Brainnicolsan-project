# utils/ai_agent.py

import os
import openai
from utils.agent_tools import get_portfolio_list, get_portfolio_metrics, compare_two_portfolios, describe_asset

openai.api_key = os.getenv("OPENAI_API_KEY")  # Or set manually here

SYSTEM_PROMPT = """
You are a financial portfolio assistant. You have access to portfolio NAVs, asset metadata, and price data. Answer questions clearly and concisely. If you don't know something, say so.
"""

def get_ai_response(prompt, metadata, price_data, navs):
    portfolio_list = get_portfolio_list(navs)
    full_prompt = SYSTEM_PROMPT + f"""

Portfolio List: {portfolio_list}
User Question: {prompt}
"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": full_prompt}
            ]
        )
        return response.choices[0].message['content']
    except Exception as e:
        return f"⚠️ Error: {str(e)}"

# Optionally extend this to LangChain if more tool calling is needed
