import json
import os
import time
from web3 import Web3

w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))

# Load Arb Contract
if not os.path.exists("arb_deployment.json"):
    print("❌ Error: arb_deployment.json not found. Run deploy_arb.py first!")
    exit()

with open("arb_deployment.json", "r") as f:
    data = json.load(f)
    arb_address = data["address"]
    arb_abi = data["abi"]

arb_bot = w3.eth.contract(address=arb_address, abi=arb_abi)
owner = w3.eth.accounts[0]

# Config (WETH-USDC Pair on Mainnet)
# We borrow WETH from this pair
WETH_USDC_PAIR = "0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc"

print("--- ⚖️ ARBITRAGE BOT ACTIVATED ---")

while True:
    try:
        print("🔍 Checking for price gap...")
        
        try:
            # Try to borrow 1 ETH
            tx = arb_bot.functions.startFlashArbitrage(
                WETH_USDC_PAIR, 
                w3.to_wei(1, 'ether')
            ).transact({
                "from": owner,
                "gas": 500000
            })
            print(f"✅ FLASH LOAN EXECUTED! Tx: {tx.hex()}")
            print("💰 Profit secured (Simulation).")
            break
            
        except Exception as e:
            # Revert means no profit (or loan failed)
            print(f"   Loan Reverted (Normal if no profit). Retrying...")
            
        time.sleep(2)

    except KeyboardInterrupt:
        break