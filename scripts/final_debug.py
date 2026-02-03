import json
from web3 import Web3

# 1. Connect
w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))

# 2. Load Contract
try:
    with open("arb_deployment.json", "r") as f:
        data = json.load(f)
        arb_address = data["address"]
        arb_abi = data["abi"]
    arb_contract = w3.eth.contract(address=arb_address, abi=arb_abi)
except:
    print("❌ Error: arb_deployment.json not found.")
    exit()

owner = w3.eth.accounts[0]

# --- CONFIGURATION ---
# We MUST target SushiSwap (The Cheap Exchange)
# SushiSwap WETH/USDC Pair Address
SUSHI_PAIR = w3.to_checksum_address("0x397FF1542f962076d0BFE58eA6658d8fC4924960")
AMOUNT = w3.to_wei(10, 'ether')

print(f"--- 🕵️ FINAL DEBUGGER ---")
print(f"Contract: {arb_address}")
print(f"Target:   SushiSwap Pair ({SUSHI_PAIR[:8]}...)")

try:
    # 3. Simulate Transaction
    print("🚀 Simulating Flash Swap...")
    
    # Using .call() to get the revert string
    arb_contract.functions.startFlashArbitrage(
        SUSHI_PAIR, 
        AMOUNT
    ).call({"from": owner})
    
    print("✅ SIMULATION PASSED: The trade should work!")
    print("   If manual_execute.py fails, check the address inside that file.")

except Exception as e:
    # 4. Analyze Error
    print("\n❌ REVERT DETECTED!")
    print("-----------------------------")
    msg = str(e)
    
    if "UniswapV2: LOCKED" in msg:
        print("🔎 REASON: LOCKED (You are borrowing from Uniswap instead of Sushi!)")
    elif "Not enough profit" in msg:
        print("🔎 REASON: Not Enough Profit (The gap isn't big enough).")
    elif "No WETH borrowed" in msg:
        print("🔎 REASON: Token Order Error (The pair didn't give us WETH).")
    else:
        print(f"🔎 RAW ERROR: {msg}")