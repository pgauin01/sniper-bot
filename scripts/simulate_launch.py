import json
import time
from web3 import Web3
from solcx import compile_standard, install_solc

# 1. Connect
w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
deployer = w3.eth.accounts[0]

# 2. Compile MockToken
with open("./contracts/MockToken.sol", "r") as f:
    source = f.read()

compiled = compile_standard(
    {
        "language": "Solidity",
        "sources": {"MockToken.sol": {"content": source}},
        "settings": {
            "outputSelection": {"*": {"*": ["abi", "evm.bytecode"]}},
             "remappings": ["@openzeppelin=./node_modules/@openzeppelin"] #
        },
    },
    solc_version="0.8.20"
)

bytecode = compiled["contracts"]["MockToken.sol"]["MockToken"]["evm"]["bytecode"]["object"]
abi = compiled["contracts"]["MockToken.sol"]["MockToken"]["abi"]

# 3. Deploy Token
print("--- 👨‍💻 DEV: Deploying Fake Token... ---")
MockToken = w3.eth.contract(abi=abi, bytecode=bytecode)
tx_hash = MockToken.constructor().transact({"from": deployer})
receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
token_address = receipt.contractAddress
print(f"✅ Token Deployed at: {token_address}")

# 4. Add Liquidity (The Trigger Event)
# We need the Uniswap Router ABI to call 'addLiquidityETH'
# (We use a simplified interface for Python)
router_address = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"
router_abi = [
    {
        "name": "addLiquidityETH",
        "inputs": [
            {"name": "token", "type": "address"},
            {"name": "amountTokenDesired", "type": "uint256"},
            {"name": "amountTokenMin", "type": "uint256"},
            {"name": "amountETHMin", "type": "uint256"},
            {"name": "to", "type": "address"},
            {"name": "deadline", "type": "uint256"}
        ],
        "outputs": [],
        "stateMutability": "payable",
        "type": "function"
    },
    # We also need 'approve' on the token
    {
        "name": "approve",
        "inputs": [{"name": "spender", "type": "address"}, {"name": "amount", "type": "uint256"}],
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    }
]

router = w3.eth.contract(address=router_address, abi=router_abi)
token = w3.eth.contract(address=token_address, abi=router_abi) # Reuse ABI for approve

print("--- 👨‍💻 DEV: Approving Uniswap... ---")
# Approve Router to spend our tokens
token.functions.approve(router_address, 2**256 - 1).transact({"from": deployer})

print("--- 👨‍💻 DEV: Adding Liquidity (LAUNCHING) in 5 seconds... ---")
time.sleep(5) 

# Add Liquidity: 100,000 Tokens + 10 ETH
tx = router.functions.addLiquidityETH(
    token_address,
    w3.to_wei(100000, 'ether'), # 100k Tokens
    0, 0, # Min amounts (0 for test)
    deployer,
    int(time.time()) + 600
).transact({
    "from": deployer,
    "value": w3.to_wei(10, 'ether'),
    "gas": 4000000
})

print(f"🚀 LIQUIDITY ADDED! Tx: {tx.hex()}")