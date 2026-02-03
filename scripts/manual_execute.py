import json
import time
from web3 import Web3

# 1. Connect
w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))

# 2. Load the NEW Contract Address
with open("arb_deployment.json", "r") as f:
    data = json.load(f)
    arb_address = data["address"]
    arb_abi = data["abi"]

arb_contract = w3.eth.contract(address=arb_address, abi=arb_abi)
owner = w3.eth.accounts[0]

# Config
WETH_USDC_PAIR = w3.to_checksum_address("0x397FF1542f962076d0BFE58eA6658d8fC4924960")

print(f"--- ⚡ MANUAL FLASH LOAN EXECUTION ---")
print(f"Contract: {arb_address}")

try:
    # 3. Execute Flash Loan (Borrow 10 WETH)
    print("🚀 Sending Transaction...")
    tx_hash = arb_contract.functions.startFlashArbitrage(
        WETH_USDC_PAIR, 
        w3.to_wei(10, 'ether')
    ).transact({
        "from": owner, 
        "gas": 1000000 
    })
    
    print(f"✅ Tx Sent: {tx_hash.hex()}")
    
    # 4. Wait for Receipt
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    
    if receipt.status == 1:
        print("🎉 SUCCESS! Transaction confirmed.")
        
        # Check Profit Immediately
        weth_token = w3.eth.contract(address="0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2", abi=[{"name": "balanceOf", "inputs": [{"name": "account", "type": "address"}], "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"}])
        bal = weth_token.functions.balanceOf(arb_address).call()
        print(f"💰 NEW CONTRACT BALANCE: {w3.from_wei(bal, 'ether')} WETH")
        
    else:
        print("❌ FAILED: Transaction Reverted.")
        print("   (Reason: Usually not enough profit to pay back loan, or stale contract)")

except Exception as e:
    print(f"❌ ERROR: {e}")