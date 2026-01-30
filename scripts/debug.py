import json
from web3 import Web3

# 1. Connect
w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))

# 2. Get the latest block and transaction
block = w3.eth.get_block('latest')
latest_tx_hash = block['transactions'][0] # Get the last tx (your snipe)
receipt = w3.eth.get_transaction_receipt(latest_tx_hash)

print(f"🕵️‍♂️ Debugging Tx: {latest_tx_hash.hex()}")
print(f"   Status: {receipt['status']} (1=Success, 0=Fail)")
print(f"   Gas Used: {receipt['gasUsed']}")
print(f"   Logs Generated: {len(receipt['logs'])}")

# 3. Check where the ETH went
with open("sniper_deployment.json", "r") as f:
    data = json.load(f)
    sniper_address = data["address"]

# Load the contract to read its state variables
sniper_abi = data["abi"]
sniper_contract = w3.eth.contract(address=sniper_address, abi=sniper_abi)

# Check 1: Did the ETH get stuck in the Sniper contract?
bot_eth = w3.from_wei(w3.eth.get_balance(sniper_address), 'ether')
print(f"🤖 Bot ETH Balance: {bot_eth} ETH")

# Check 2: What Router address is the contract actually using?
try:
    actual_router = sniper_contract.functions.routerAddress().call()
    print(f"🔗 Contract is using Router: {actual_router}")
    
    # Verify if that router has code
    code_size = len(w3.eth.get_code(actual_router))
    if code_size == 0:
        print("❌ CRITICAL FAILURE: The Router address in the contract is EMPTY!")
    else:
        print(f"✅ Router seems valid (Code size: {code_size})")

except Exception as e:
    print(f"⚠️ Could not read router address: {e}")

# Check 3: Analyze Logs
if len(receipt['logs']) == 0:
    print("❌ NO LOGS: This means Uniswap was never actually triggered.")
else:
    print("✅ LOGS FOUND: Uniswap did something. The tokens might be somewhere else.")