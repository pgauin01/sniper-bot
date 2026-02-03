import streamlit as st
import pandas as pd
import json
import os
from web3 import Web3

# --- SETUP ---
st.set_page_config(page_title="🦅 Sniper Bot Dashboard", layout="wide")
st.title("🦅 Sniper Bot Command Center")

# Connect to Ganache
w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
if not w3.is_connected():
    st.error("❌ Ganache NOT connected. Is it running?")
    st.stop()

# Load Contract
with open("sniper_deployment.json", "r") as f:
    data = json.load(f)
    sniper_address = data["address"]
    sniper_abi = data["abi"]

sniper = w3.eth.contract(address=sniper_address, abi=sniper_abi)
owner = w3.eth.accounts[0]

# --- SIDEBAR CONTROLS ---
st.sidebar.header("🕹️ Controls")
st.sidebar.write(f"**Bot Wallet:** `{sniper_address[:6]}...{sniper_address[-4:]}`")

if st.sidebar.button("🔄 Refresh Data"):
    st.rerun()

# --- WITHDRAW BUTTON (NEW) ---
if st.sidebar.button("💸 Withdraw Profit"):
    try:
        tx = sniper.functions.withdrawETH().transact({'from': owner})
        st.sidebar.success(f"Withdrawn! Tx: {tx.hex()[:10]}...")
        st.rerun()
    except Exception as e:
        st.sidebar.error(f"Withdraw Failed: {e}")

# --- MAIN DASHBOARD ---
# 1. Load Data
if not os.path.exists("sniped_tokens.txt"):
    st.warning("No snipe history found.")
    st.stop()

with open("sniped_tokens.txt", "r") as f:
    tokens = [line.strip() for line in f.readlines() if line.strip()]

# 2. Fetch Live Stats
portfolio_data = []
total_est_token_value = 0

# --- NEW: Get Realized ETH Profit ---
contract_eth_balance_wei = w3.eth.get_balance(sniper_address)
contract_eth_balance = w3.from_wei(contract_eth_balance_wei, 'ether')

for token_addr in tokens:
    try:
        # Get Balance
        balance = sniper.functions.getTokenBalance(token_addr).call()
        
        # Get ETH Value (Estimate)
        eth_val = 0
        status = "❌ Sold (Profit Taken)" # Default status if balance is 0
        
        if balance > 0:
            amounts = sniper.functions.getAmountsOut(token_addr, balance).call()
            eth_val = w3.from_wei(amounts[1], 'ether')
            total_est_token_value += eth_val
            status = "✅ Holding"

        portfolio_data.append({
            "Token Address": token_addr,
            "Balance": balance,
            "Value (ETH)": float(eth_val),
            "Status": status
        })
    except Exception as e:
        portfolio_data.append({
            "Token Address": token_addr,
            "Balance": 0,
            "Value (ETH)": 0,
            "Status": "⚠️ Error / Rug"
        })

df = pd.DataFrame(portfolio_data)

# 3. Metrics Row
col1, col2, col3 = st.columns(3)

col1.metric("💰 Realized Profit (ETH)", f"{contract_eth_balance:.4f} ETH", "Available to Withdraw")
col2.metric("📊 Unrealized Token Value", f"{total_est_token_value:.4f} ETH")
col3.metric("Total Snipes", len(tokens))

st.subheader("💼 Trade History")
st.dataframe(df, use_container_width=True)

# 4. Raw Logs
with st.expander("View Raw Token List"):
    st.text_area("Log Data", value="\n".join(tokens), height=100)