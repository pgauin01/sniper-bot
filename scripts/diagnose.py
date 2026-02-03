from web3 import Web3

# 1. Connect
w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))

# 2. The Failed Transaction (From your logs)
TX_HASH = "0x8c80abea72041f26bc5185885861f7978cd3289ef25f5034455be1fc10ecc012"

print(f"--- 🕵️‍♂️ DIAGNOSING TX: {TX_HASH} ---")

try:
    # Get Receipt
    receipt = w3.eth.get_transaction_receipt(TX_HASH)
    
    if receipt is None:
        print("❌ Receipt not found. Transaction might still be pending or dropped.")
        exit()

    print(f"Status: {receipt['status']} (1=Success, 0=Fail)")
    print(f"Gas Used: {receipt['gasUsed']}")

    if receipt['status'] == 0:
        print("\n❌ CONCLUSION: The transaction REVERTED.")
        print("Possible causes:")
        print("1. 'receive()' missing: Did Uniswap try to refund dust ETH?")
        print("2. Slippage: Did the price move too fast?")
        print("3. K-Error: Pool reserves issue.")
        
        # Advanced: Try to replay the transaction to get the error message
        print("\n🔍 Attempting to Replay Transaction for Error Message...")
        tx = w3.eth.get_transaction(TX_HASH)
        
        # Prepare replay parameters
        replay_params = {
            'to': tx['to'],
            'from': tx['from'],
            'value': tx['value'],
            'data': tx['input'],
            'gas': tx['gas'],
            'gasPrice': tx['gasPrice'],
        }
        
        try:
            # call() simulates the transaction locally and returns the revert string
            w3.eth.call(replay_params, receipt['blockNumber'])
        except Exception as e:
            print(f"\n⚠️ REVERT REASON FOUND:\n{e}")

    else:
        print("✅ Status is 1 (Success). If balance is 0, check the token contract address.")

except Exception as e:
    print(f"Error reading tx: {e}")