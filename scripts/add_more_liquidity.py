import time
from web3 import Web3

w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
deployer = w3.eth.accounts[0]

# 1. PASTE ONE OF YOUR EXISTING TOKENS HERE
# (I took the last one from your portfolio check)
EXISTING_TOKEN = "0xBA0ACb50fb14A59d8625D4eA164D88B245BcdBF2" 

router_address = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"
router_abi = [{"name": "addLiquidityETH", "inputs": [{"name": "token", "type": "address"}, {"name": "amountTokenDesired", "type": "uint256"}, {"name": "amountTokenMin", "type": "uint256"}, {"name": "amountETHMin", "type": "uint256"}, {"name": "to", "type": "address"}, {"name": "deadline", "type": "uint256"}], "outputs": [], "stateMutability": "payable", "type": "function"}, {"name": "approve", "inputs": [{"name": "spender", "type": "address"}, {"name": "amount", "type": "uint256"}], "outputs": [{"name": "", "type": "bool"}], "type": "function"}]

router = w3.eth.contract(address=router_address, abi=router_abi)
token = w3.eth.contract(address=EXISTING_TOKEN, abi=router_abi)

print(f"--- 💧 ADDING MORE LIQUIDITY TO: {EXISTING_TOKEN} ---")

# Approve
print("Approving...")
token.functions.approve(router_address, 2**256 - 1).transact({"from": deployer})

# Add Liquidity
print("Adding Liquidity (Bot should IGNORE this)...")
router.functions.addLiquidityETH(
    EXISTING_TOKEN,
    w3.to_wei(1000, 'ether'), # 1000 Tokens
    0, 0,
    deployer,
    int(time.time()) + 600
).transact({
    "from": deployer,
    "value": w3.to_wei(1, 'ether'),
    "gas": 4000000
})

print("✅ Liquidity Added! Check your bot terminal.")