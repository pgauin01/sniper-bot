import json
from web3 import Web3
from decimal import Decimal  # <--- NEW IMPORT

# 1. Connect
w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))

# 2. Load Configuration
with open("sniper_deployment.json", "r") as f:
    data = json.load(f)
    sniper_address = data["address"]
    sniper_abi = data["abi"]

sniper = w3.eth.contract(address=sniper_address, abi=sniper_abi)
owner = w3.eth.accounts[0]

print(f"--- 📊 SNIPER PROFIT/LOSS REPORT ---")
print(f"Sniper Contract: {sniper_address}")
print(f"Owner Wallet:    {owner}")

# 3. Scan History (Last 100 Blocks)
current_block = w3.eth.block_number
start_block = max(0, current_block - 100) 

print(f"\nScanning blocks {start_block} to {current_block} for trades...")

total_invested_eth = Decimal(0)
total_gas_eth = Decimal(0)
trade_count = 0

for block_num in range(start_block, current_block + 1):
    block = w3.eth.get_block(block_num, full_transactions=True)
    
    for tx in block.transactions:
        if tx['from'] == owner and tx['to'] == sniper_address:
            trade_count += 1
            
            # 1. Investment
            eth_value = w3.from_wei(tx['value'], 'ether')
            total_invested_eth += eth_value
            
            # 2. Gas Cost
            receipt = w3.eth.get_transaction_receipt(tx['hash'])
            gas_cost_wei = receipt['gasUsed'] * tx['gasPrice']
            gas_cost_eth = w3.from_wei(gas_cost_wei, 'ether')
            total_gas_eth += gas_cost_eth
            
            print(f"   [Tx Found] Val: {eth_value:.4f} ETH | Gas: {gas_cost_eth:.6f} ETH")

# 4. Calculate Returns
contract_balance_wei = w3.eth.get_balance(sniper_address)
contract_balance_eth = w3.from_wei(contract_balance_wei, 'ether')

# 5. Calculate Net P/L
total_spent = total_invested_eth + total_gas_eth
net_profit = contract_balance_eth - total_spent

print("-" * 40)
print(f"📈 TRADING SUMMARY")
print(f"   Trades Found:     {trade_count}")
print(f"   Total Invested:   {total_invested_eth:.6f} ETH (Buys)")
print(f"   Total Gas Fees:   {total_gas_eth:.6f} ETH")
print(f"   --------------------------------")
print(f"   TOTAL SPENT:      {total_spent:.6f} ETH")
print("-" * 40)
print(f"💰 RETURNS")
print(f"   Contract Balance: {contract_balance_eth:.6f} ETH (Realized Gains)")
print("-" * 40)

if net_profit > 0:
    print(f"✅ NET PROFIT:       +{net_profit:.6f} ETH 🚀")
else:
    print(f"🔻 NET LOSS:         {net_profit:.6f} ETH")

# --- FIX: USE Decimal('0.5') INSTEAD OF 0.5 ---
if total_invested_eth > 0 and contract_balance_eth < (total_invested_eth * Decimal('0.5')):
    print("\n⚠️  Note: Your balance is low. Do you have unsold tokens?")
    print("    Run 'python scripts/check_portfolio.py' to check.")