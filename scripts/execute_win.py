import json
from web3 import Web3

# 1. Connect
w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))

# 2. Load Deployment
try:
    with open("arb_deployment.json", "r") as f:
        data = json.load(f)
        arb_address = data["address"]
        arb_abi = data["abi"]
    arb_contract = w3.eth.contract(address=arb_address, abi=arb_abi)
except:
    print("❌ Error: Deployment file not found.")
    exit()

owner = w3.eth.accounts[0]

# --- THE CRITICAL FIX ---
# We force the script to use SushiSwap. 
# If we used Uniswap here, it would revert with "LOCKED".
SUSHI_PAIR = w3.to_checksum_address("0x397FF1542f962076d0BFE58eA6658d8fC4924960")
AMOUNT = w3.to_wei(10, 'ether')

print(f"--- 🏆 WINNING TRADE EXECUTION ---")
print(f"Bot Address: {arb_address}")
print(f"Target Pair: SushiSwap (CORRECT)")

try:
    # 3. Check for the 'Internal Math' Fix
    # We simulate a call. If this reverts, the contract code is still old.
    print("🔎 Verifying Contract Logic...")
    arb_contract.functions.startFlashArbitrage(SUSHI_PAIR, AMOUNT).call({"from": owner})
    print("✅ Logic Check Passed: Contract is ready.")

    # 4. Execute Real Transaction
    print("🚀 Sending Transaction...")
    tx_hash = arb_contract.functions.startFlashArbitrage(
        SUSHI_PAIR, 
        AMOUNT
    ).transact({
        "from": owner, 
        "gas": 1000000 
    })
    
    print(f"✅ Tx Sent: {tx_hash.hex()}")
    
    # 5. Wait for Receipt
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    
    if receipt.status == 1:
        print("🎉 SUCCESS! Trade Confirmed.")
        
        # Check Profits
        usdc_abi = [{"name": "balanceOf", "inputs": [{"name": "account", "type": "address"}], "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"}]
        usdc = w3.eth.contract(address="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48", abi=usdc_abi)
        bal = usdc.functions.balanceOf(arb_address).call()
        print(f"💰 FINAL PROFIT: ${bal / 1e6:,.2f} USDC")
        
    else:
        print("❌ FAILED: Transaction still reverted.")

except Exception as e:
    print("\n❌ EXECUTION ERROR!")
    print(e)
    if "revert" in str(e):
        print("\n👉 DIAGNOSIS: If this failed, your ArbSniper.sol might still be the OLD version.")
        print("   Solution: Copy the code from Step 2 below and Redeploy.")