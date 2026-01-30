import json
from web3 import Web3
import os
from solcx import compile_standard, install_solc

# 1. Calculate the absolute path to the 'node_modules' folder
# This assumes your script is in 'scripts/' and node_modules is one level up.
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir) 
node_modules_path = os.path.join(project_root, "node_modules")

# Verify the path exists (Debugging step)
if not os.path.exists(node_modules_path):
    print(f"CRITICAL ERROR: Could not find node_modules at: {node_modules_path}")
    print("Did you run 'npm install @openzeppelin/contracts' in the project root?")

# 2. Read the Solidity file
with open("./contracts/Sniper.sol", "r") as file:
    sniper_bot_file = file.read()

# 3. Compile with Absolute Path Remapping
# 3. Compile with Absolute Path Remapping AND specific EVM version
compiled_sol = compile_standard(
    {
        "language": "Solidity",
        "sources": {"Sniper.sol": {"content": sniper_bot_file}},
        "settings": {
            # ADD THIS LINE ▼
            "evmVersion": "paris", 
            "optimizer": { "enabled": True, "runs": 200 },
            "outputSelection": {
                "*": {"*": ["abi", "metadata", "evm.bytecode", "evm.sourceMap"]}
            },
            "remappings": [
                f"@openzeppelin={os.path.join(node_modules_path, '@openzeppelin')}"
            ]
        },
    },
    solc_version="0.8.20",
    allow_paths=[project_root]
)

print("Compilation Successful!")

# Extract Bytecode and ABI
bytecode = compiled_sol["contracts"]["Sniper.sol"]["Sniper"]["evm"]["bytecode"]["object"]
abi = compiled_sol["contracts"]["Sniper.sol"]["Sniper"]["abi"]

# 4. CONNECT: Connect to Ganache
# Ganache usually runs on 127.0.0.1:8545
w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))

# Check connection
if w3.is_connected():
    print("Connected to Ganache!")
else:
    print("Connection failed. Is Ganache running?")
    exit()

# 5. DEPLOY: Put it on the chain
# We need an account to sign the transaction. 
# In Ganache, the first account (index 0) is unlocked by default in some versions,
# but usually, we just use the address because Ganache is 'permissive' by default.
# ... (Imports and Compile steps remain the same) ...

# 5. DEPLOY
deployer_account = w3.eth.accounts[0]
print(f"Deploying from: {deployer_account}")

SniperContract = w3.eth.contract(abi=abi, bytecode=bytecode)

# CHANGE: No arguments passed to constructor()
tx_hash = SniperContract.constructor().transact({
    "from": deployer_account,
    "gas": 2000000
})

tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
print(f"✅ Contract Deployed at: {tx_receipt.contractAddress}")

# Save deployment
with open("sniper_deployment.json", "w") as outfile:
    json.dump({"address": tx_receipt.contractAddress, "abi": abi}, outfile)