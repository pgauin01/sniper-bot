import json
from web3 import Web3

# 1. Connect
w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))

# 2. Load Deployment Data
with open("sniper_deployment.json", "r") as f:
    data = json.load(f)
    sniper_address = data["address"]
    sniper_abi = data["abi"]

sniper = w3.eth.contract(address=sniper_address, abi=sniper_abi)
owner = w3.eth.accounts[0]

# 3. Setup USDC (Target Token)
# This is the Real USDC address on Mainnet
USDC_ADDRESS = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"

# We need a tiny ABI just to check our balance
erc20_abi = [
    {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"}
]
usdc = w3.eth.contract(address=USDC_ADDRESS, abi=erc20_abi)

# Helper function to print nicely
def check_balance():
    raw_bal = usdc.functions.balanceOf(sniper_address).call()
    decimals = usdc.functions.decimals().call()
    print(f"💰 Sniper Bot Balance: {raw_bal / 10**decimals} USDC")

# --- EXECUTION ---
print("--- 🔫 STARTING SNIPE ---")
check_balance()

print("🚀 Sending transaction to Uniswap...")
try:
    # We send 1 ETH with the transaction (value=1 ether)
    # The contract will swap this 1 ETH for USDC
    tx_hash = sniper.functions.snipe(
        USDC_ADDRESS, 
        0 # amountOutMin (0 for testing, unsafe in production!)
    ).transact({
        "from": owner,
        "value": w3.to_wei(1, 'ether'), 
        "gas": 300000
    })
    
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    if receipt['status'] == 1:
        print("✅ Transaction SUCCESS! (Status 1)")
    else:
     print("❌ Transaction REVERTED! (Status 0)")
    
    print("✅ Transaction Confirmed!")
    
    check_balance()
    print("🎉 Success! You just interacted with Mainnet Uniswap locally.")

except Exception as e:
    print(f"❌ Error: {e}")