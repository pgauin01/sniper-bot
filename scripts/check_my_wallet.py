from web3 import Web3

# 1. Connect
w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))

# 2. Get Owner Wallet
owner_address = w3.eth.accounts[0]

# 3. Check Balance
balance_wei = w3.eth.get_balance(owner_address)
balance_eth = w3.from_wei(balance_wei, 'ether')

print(f"--- 🏦 WALLET CHECK ---")
print(f"Owner Address: {owner_address}")
print(f"Current Balance: {balance_eth:.4f} ETH")