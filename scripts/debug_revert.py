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
    print("❌ Error: Could not load deployment file.")
    exit()

owner = w3.eth.accounts[0]

# --- CRITICAL UPDATE: TARGET SUSHISWAP PAIR ---
# We are borrowing from Sushi now, so we must debug against THIS address.
SUSHI_PAIR = w3.to_checksum_address("0x397FF1542f962076d0BFE58eA6658d8fC4924960")
amount_to_borrow = w3.to_wei(10, 'ether')

print(f"--- 🕵️ REVERT DEBUGGER (FLASH SWAP) ---")
print(f"Contract: {arb_address}")
print(f"Target Pair: SushiSwap (WETH/USDC)")

try:
    # 3. Simulate the Call
    print("🚀 Simulating Transaction...")
    
    arb_contract.functions.startFlashArbitrage(
        SUSHI_PAIR, 
        amount_to_borrow
    ).call({"from": owner})
    
    print("✅ SIMULATION SUCCESS: Logic is perfect.")

except Exception as e:
    # 4. Extract the Revert Reason
    print("\n❌ CRITICAL FAILURE DETECTED!")
    print("-----------------------------")
    error_str = str(e)
    
    # Common Revert strings
    if "Not enough profit" in error_str:
        print("🔎 REASON: Profit Check Failed (You are losing money on the trade).")
    elif "UniswapV2: K" in error_str:
        print("🔎 REASON: UniswapV2 'K' Error (Fee calculation is wrong).")
    elif "TransferHelper" in error_str:
        print("🔎 REASON: Token Transfer Failed (Allowance or Balance issue).")
    else:
        print(f"🔎 RAW ERROR: {error_str}")