import json
from web3 import Web3

w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))

with open("arb_deployment.json", "r") as f:
    data = json.load(f)
    contract = w3.eth.contract(address=data["address"], abi=data["abi"])

owner = w3.eth.accounts[0]
SUSHI_PAIR = w3.to_checksum_address("0x397FF1542f962076d0BFE58eA6658d8fC4924960")
AMOUNT = w3.to_wei(10, 'ether')

print(f"--- 🕵️ TRACE EXECUTION ---")
try:
    # We use .transact() here to generate a receipt we can inspect
    # But if it reverts, we might lose logs.
    # So we force a .call() first to see logs live.
    
    tx = contract.functions.startFlashArbitrage(SUSHI_PAIR, AMOUNT).transact({"from": owner, "gas": 3000000})
    receipt = w3.eth.wait_for_transaction_receipt(tx)
    print("✅ SUCCESS! Logs:")
    for log in receipt['logs']:
        print(log)

except Exception as e:
    print("\n❌ CRASH DETECTED! Reading Flight Recorder...")
    
    # Re-run as call to extract events? No, call reverts don't show events easily in Web3.py
    # We rely on the error message sometimes leaking data.
    print(e)
    
    print("\n--- ATTEMPTING TO READ LOGS VIA SIMULATION ---")
    # This is a trick to get events from a failed call
    try:
        contract.functions.startFlashArbitrage(SUSHI_PAIR, AMOUNT).call({"from": owner})
    except Exception as e2:
        print(f"Revert Reason: {e2}")