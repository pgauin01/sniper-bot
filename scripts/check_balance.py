import json
import os
from web3 import Web3

# 1. Connect
w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))

# 2. Load Sniper Address
with open("sniper_deployment.json", "r") as f:
    data = json.load(f)
    sniper_address = data["address"]

# 3. Load Sniped Tokens from File
tokens_file = "sniped_tokens.txt"

if not os.path.exists(tokens_file):
    print("❌ No 'sniped_tokens.txt' found. Run the bot and snipe something first!")
    exit()

with open(tokens_file, "r") as f:
    # Read lines and remove whitespace/newlines
    tokens = [line.strip() for line in f.readlines() if line.strip()]

print(f"\n--- 💼 PORTFOLIO CHECK (Owner: {sniper_address}) ---")
print(f"{'TOKEN ADDRESS':<45} | {'SYMBOL':<6} | {'BALANCE':<15}")
print("-" * 75)

# Standard ERC20 ABI
erc20_abi = [
    {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "type": "function"}
]

total_value = 0

for token_addr in tokens:
    try:
        contract = w3.eth.contract(address=token_addr, abi=erc20_abi)
        
        symbol = contract.functions.symbol().call()
        decimals = contract.functions.decimals().call()
        raw_bal = contract.functions.balanceOf(sniper_address).call()
        
        human_bal = raw_bal / (10 ** decimals)
        
        print(f"{token_addr:<45} | {symbol:<6} | {human_bal:,.2f}")
        
    except Exception as e:
        print(f"{token_addr:<45} | ERROR  | Could not read")

print("-" * 75)