import json
import os
from web3 import Web3
from solcx import compile_standard

w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
deployer = w3.eth.accounts[0]

# Compile
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
node_modules = os.path.join(project_root, "node_modules")

with open("./contracts/ArbSniper.sol", "r") as f:
    source = f.read()

compiled = compile_standard(
    {
        "language": "Solidity",
        "sources": {"ArbSniper.sol": {"content": source}},
        "settings": {
            "outputSelection": {"*": {"*": ["abi", "evm.bytecode"]}},
            "remappings": [f"@openzeppelin={os.path.join(node_modules, '@openzeppelin')}"]
        },
    },
    solc_version="0.8.20",
    allow_paths=[project_root]
)

bytecode = compiled["contracts"]["ArbSniper.sol"]["ArbSniper"]["evm"]["bytecode"]["object"]
abi = compiled["contracts"]["ArbSniper.sol"]["ArbSniper"]["abi"]

# Deploy
print(f"🚀 Deploying ArbSniper from {deployer}...")
ArbContract = w3.eth.contract(abi=abi, bytecode=bytecode)
tx_hash = ArbContract.constructor().transact({"from": deployer})
receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

print(f"✅ ArbSniper Deployed at: {receipt.contractAddress}")

# Save Address
with open("arb_deployment.json", "w") as f:
    json.dump({"address": receipt.contractAddress, "abi": abi}, f)