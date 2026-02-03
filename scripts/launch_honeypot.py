import json
import time
from web3 import Web3
from solcx import compile_standard

# 1. Connect
w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
deployer = w3.eth.accounts[0]

# 2. Compile HoneypotToken (The SCAM)
with open("./contracts/HoneypotToken.sol", "r") as f:
    source = f.read()

compiled = compile_standard(
    {
        "language": "Solidity",
        "sources": {"HoneypotToken.sol": {"content": source}},
        "settings": {
            "outputSelection": {"*": {"*": ["abi", "evm.bytecode"]}},
             "remappings": ["@openzeppelin=./node_modules/@openzeppelin"]
        },
    },
    solc_version="0.8.20"
)

bytecode = compiled["contracts"]["HoneypotToken.sol"]["HoneypotToken"]["evm"]["bytecode"]["object"]
abi = compiled["contracts"]["HoneypotToken.sol"]["HoneypotToken"]["abi"]

# 3. Deploy Token
print("--- 🐝 DEV: Deploying HONEYPOT Token... ---")
HoneypotToken = w3.eth.contract(abi=abi, bytecode=bytecode)
tx_hash = HoneypotToken.constructor().transact({"from": deployer})
receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
token_address = receipt.contractAddress
print(f"✅ Scam Token Deployed at: {token_address}")

# 4. Add Liquidity (The Trap)
router_address = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"
router_abi = [
    {"name": "addLiquidityETH", "inputs": [{"name": "token", "type": "address"}, {"name": "amountTokenDesired", "type": "uint256"}, {"name": "amountTokenMin", "type": "uint256"}, {"name": "amountETHMin", "type": "uint256"}, {"name": "to", "type": "address"}, {"name": "deadline", "type": "uint256"}], "outputs": [], "stateMutability": "payable", "type": "function"},
    {"name": "approve", "inputs": [{"name": "spender", "type": "address"}, {"name": "amount", "type": "uint256"}], "outputs": [{"name": "", "type": "bool"}], "type": "function"}
]

router = w3.eth.contract(address=router_address, abi=router_abi)
token = w3.eth.contract(address=token_address, abi=router_abi)

print("--- 🐝 DEV: Arming the Trap (Adding Liquidity)... ---")
token.functions.approve(router_address, 2**256 - 1).transact({"from": deployer})
time.sleep(2) 

router.functions.addLiquidityETH(
    token_address,
    w3.to_wei(100000, 'ether'),
    0, 0,
    deployer,
    int(time.time()) + 600
).transact({
    "from": deployer,
    "value": w3.to_wei(10, 'ether'),
    "gas": 4000000
})

print(f"🚨 TRAP SET! Liquidity Added. Bot should detect this.")