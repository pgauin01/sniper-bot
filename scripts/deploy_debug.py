import json
from web3 import Web3
from solcx import compile_standard, install_solc

install_solc("0.8.0")

def deploy():
    w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
    with open("contracts/ArbDebug.sol", "r") as f:
        source = f.read()

    compiled_sol = compile_standard({
        "language": "Solidity",
        "sources": {"ArbDebug.sol": {"content": source}},
        "settings": {"outputSelection": {"*": {"*": ["abi", "evm.bytecode"]}}}
    }, solc_version="0.8.0")

    bytecode = compiled_sol["contracts"]["ArbDebug.sol"]["ArbDebug"]["evm"]["bytecode"]["object"]
    abi = compiled_sol["contracts"]["ArbDebug.sol"]["ArbDebug"]["abi"]

    deployer = w3.eth.accounts[0]
    ArbDebug = w3.eth.contract(abi=abi, bytecode=bytecode)
    
    print("🚀 Deploying DEBUG Contract...")
    tx_hash = ArbDebug.constructor().transact({"from": deployer})
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    
    print(f"✅ DEBUGGER DEPLOYED AT: {tx_receipt.contractAddress}")
    
    # Save for the runner
    with open("arb_deployment.json", "w") as f:
        json.dump({"address": tx_receipt.contractAddress, "abi": abi}, f)

if __name__ == "__main__":
    deploy()