import streamlit as st
import time
import json
from web3 import Web3
import pandas as pd

st.set_page_config(page_title="⚡ Flash Arb Dashboard", layout="wide")
st.title("⚡ Flash Loan Arbitrage Console")

# 1. Connect
w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
if not w3.is_connected():
    st.error("❌ Ganache NOT connected.")
    st.stop()

# 2. Config
WETH = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
USDC = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
WETH_USDC_PAIR = "0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc"
UNISWAP_ROUTER = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"
SUSHISWAP_ROUTER = "0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F"

router_abi = [{"name": "getAmountsOut", "inputs": [{"name": "amountIn", "type": "uint256"}, {"name": "path", "type": "address[]"}], "outputs": [{"name": "amounts", "type": "uint256[]"}], "stateMutability": "view", "type": "function"}]

uniswap = w3.eth.contract(address=UNISWAP_ROUTER, abi=router_abi)
sushi = w3.eth.contract(address=SUSHISWAP_ROUTER, abi=router_abi)

# Load Arb Contract
try:
    with open("arb_deployment.json", "r") as f:
        data = json.load(f)
        arb_address = data["address"]
        arb_abi = data["abi"]
    arb_bot = w3.eth.contract(address=arb_address, abi=arb_abi)
except:
    st.error("⚠️ Arb Contract not deployed yet.")
    st.stop()

owner = w3.eth.accounts[0]

# --- SIDEBAR ---
if st.sidebar.button("🔄 Refresh Prices"):
    st.rerun()

# --- MAIN UI ---
st.subheader("📉 Market Monitor (WETH / USDC)")

# 1. Get Prices
amount_in = w3.to_wei(1, 'ether') # 1 WETH
try:
    uni_price = uniswap.functions.getAmountsOut(amount_in, [WETH, USDC]).call()[1] / 1e6
    sushi_price = sushi.functions.getAmountsOut(amount_in, [WETH, USDC]).call()[1] / 1e6
except:
    st.warning("Connecting to chain...")
    st.stop()

diff = uni_price - sushi_price
pct_diff = (diff / sushi_price) * 100

col1, col2, col3 = st.columns(3)
col1.metric("Uniswap Price", f"${uni_price:,.2f}")
col2.metric("SushiSwap Price", f"${sushi_price:,.2f}")
col3.metric("Price Gap", f"${diff:,.2f}", f"{pct_diff:.2f}%")

# 2. Execution Zone
st.divider()
st.subheader("🚀 Execution Zone")

if diff > 100: # Only show if profitable
    st.success("✅ PROFIT OPPORTUNITY DETECTED!")
    
    if st.button("⚡ EXECUTE FLASH LOAN"):
        with st.spinner("Borrowing 10 WETH..."):
            try:
                # Borrow 10 WETH
                tx = arb_bot.functions.startFlashArbitrage(
                    WETH_USDC_PAIR, 
                    w3.to_wei(10, 'ether')
                ).transact({
                    "from": owner, 
                    "gas": 500000
                })
                st.balloons()
                st.success(f"Transaction Successful! Tx: {tx.hex()}")
            except Exception as e:
                st.error(f"Execution Failed: {e}")
else:
    st.info("Waiting for spread > $100...")

# 3. Portfolio
st.divider()
st.subheader("💰 Bot Profits")
try:
    # Check WETH balance of Bot
    erc20_abi = [{"name": "balanceOf", "inputs": [{"name": "account", "type": "address"}], "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"}]
    weth_token = w3.eth.contract(address=WETH, abi=erc20_abi)
    bot_balance = weth_token.functions.balanceOf(arb_address).call()
    st.metric("Bot WETH Balance", f"{w3.from_wei(bot_balance, 'ether'):.4f} WETH")
except:
    pass