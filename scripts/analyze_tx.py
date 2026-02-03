from web3 import Web3
from eth_abi import decode
import json

w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))

# PASTE YOUR TRANSACTION HASH HERE
TX_HASH = "9fa2c953b8e93fc17f7d61484db2b5baec46db8aea3e1075426915f78da7e776"

# Contract & Token Config
WETH = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
USDC = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"

# Load Contract Address
with open("arb_deployment.json", "r") as f:
    data = json.load(f)
    arb_address = data["address"]

print(f"--- 🕵️‍♂️ TRANSACTION FORENSICS ---")
print(f"Analyzing Tx: {TX_HASH[:10]}...")
print(f"Arb Contract: {arb_address}")

receipt = w3.eth.get_transaction_receipt(TX_HASH)

# Transfer Event Signature (ERC20)
# Topic 0: 0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef
TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"

logs = receipt['logs']
print(f"\n📄 Found {len(logs)} Events in this transaction:")

weth_in = 0
weth_out = 0

for i, log in enumerate(logs):
    # Only look at Transfer events
    if log['topics'][0].hex() == TRANSFER_TOPIC:
        # Decode Addresses (Topic 1 = From, Topic 2 = To)
        # addresses are 32 bytes in topics, we need last 20 bytes
        from_addr = w3.to_checksum_address("0x" + log['topics'][1].hex()[-40:])
        to_addr = w3.to_checksum_address("0x" + log['topics'][2].hex()[-40:])
        
        # Decode Amount (Data)
        amount = int(log['data'].hex(), 16)
        
        token_name = "UNKNOWN"
        if log['address'] == WETH: token_name = "WETH"
        if log['address'] == USDC: token_name = "USDC"

        # Check if our contract was involved
        direction = ""
        if to_addr == arb_address:
            direction = "🟢 IN "
            if token_name == "WETH": weth_in += amount
        elif from_addr == arb_address:
            direction = "🔴 OUT"
            if token_name == "WETH": weth_out += amount
        
        if direction:
            print(f"  {i}. {direction} | {amount / 1e18 if token_name == 'WETH' else amount / 1e6:.2f} {token_name} | From: {from_addr[:6]}... To: {to_addr[:6]}...")

print(f"\n--- 🧮 BALANCE SHEET ---")
print(f"Total WETH IN:  {weth_in / 1e18:.4f}")
print(f"Total WETH OUT: {weth_out / 1e18:.4f}")
print(f"Net Change:     {(weth_in - weth_out) / 1e18:.4f} WETH")

# Double Check Current Balance
erc20_abi = [{"name": "balanceOf", "inputs": [{"name": "account", "type": "address"}], "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"}]
weth_contract = w3.eth.contract(address=WETH, abi=erc20_abi)
real_bal = weth_contract.functions.balanceOf(arb_address).call()
print(f"Actual Chain Balance: {real_bal / 1e18:.4f} WETH")