import json
from web3 import Web3

w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))

# Load Contract Address
with open("arb_deployment.json", "r") as f:
    data = json.load(f)
    arb_address = data["address"]

WETH = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
erc20_abi = [{"name": "balanceOf", "inputs": [{"name": "account", "type": "address"}], "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"}]

weth = w3.eth.contract(address=WETH, abi=erc20_abi)
balance = weth.functions.balanceOf(arb_address).call()

print(f"--- 🔍 CONTRACT INSPECTION ---")
print(f"Contract: {arb_address}")
print(f"WETH Balance: {w3.from_wei(balance, 'ether')} WETH")