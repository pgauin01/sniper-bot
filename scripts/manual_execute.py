import argparse
import json
import time
from web3 import Web3

def execute(borrow_weth: float = 10.0, auto_withdraw: bool = True):
    # 1. Connect
    w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
    if not w3.is_connected():
        print("❌ Error: Ganache is not running.")
        return

    # 2. Load Deployment
    try:
        with open("arb_deployment.json", "r") as f:
            data = json.load(f)
            arb_address = data["address"]
            arb_abi = data["abi"]
        arb_contract = w3.eth.contract(address=arb_address, abi=arb_abi)
    except FileNotFoundError:
        print("❌ Error: arb_deployment.json not found. Run deploy_arb.py first.")
        return

    owner = w3.eth.accounts[0]

    usdc_abi = [{"name": "balanceOf", "inputs": [{"name": "account", "type": "address"}], "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"}]
    usdc = w3.eth.contract(address="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48", abi=usdc_abi)
    start_bal_raw = usdc.functions.balanceOf(owner).call()

    # --- CONFIGURATION ---
    WETH = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
    USDC = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
    SUSHI_FACTORY = w3.to_checksum_address("0xC0AEe478e3658e2610c5F7A4A2E1777cE9e4f2Ac")
    factory_abi = [
        {"name": "getPair", "inputs": [{"name": "tokenA", "type": "address"}, {"name": "tokenB", "type": "address"}], "outputs": [{"name": "pair", "type": "address"}], "stateMutability": "view", "type": "function"}
    ]
    factory = w3.eth.contract(address=SUSHI_FACTORY, abi=factory_abi)
    SUSHI_PAIR = factory.functions.getPair(WETH, USDC).call()
    if int(SUSHI_PAIR, 16) == 0:
        print("Error: Sushi WETH/USDC pair not found.")
        return

    BORROW_AMOUNT = w3.to_wei(borrow_weth, 'ether')


    print(f"--- ⚡ MANUAL FLASH EXECUTION ---")
    print(f"Bot Address: {arb_address}")
    print(f"Target Pair: SushiSwap ({SUSHI_PAIR})")
    print(f"Borrowing:   {borrow_weth} WETH")
    try:
        contract_owner = arb_contract.functions.owner().call()
        print(f"Contract Owner: {contract_owner}")
        print(f"Caller:         {owner}")
    except Exception:
        pass

    try:
        # 3. Preflight (catch revert reason)
        print("Preflight call...")
        arb_contract.functions.startFlashArbitrage(SUSHI_PAIR, BORROW_AMOUNT).call({"from": owner})
        print("Preflight OK.")

        # 4. Execute
        print("🚀 Sending Transaction...")
        tx_hash = arb_contract.functions.startFlashArbitrage(
            SUSHI_PAIR, 
            BORROW_AMOUNT
        ).transact({
            "from": owner, 
            "gas": 1000000
        })
        
        print(f"✅ Tx Sent: {tx_hash.hex()}")
        
        # 4. Wait for Receipt
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        if receipt.status == 1:
            print("🎉 SUCCESS! Transaction Confirmed.")
            
            # Check Contract Balance
            bal = usdc.functions.balanceOf(arb_address).call()
            print(f"💰 BOT BALANCE: ${bal / 1e6:,.2f} USDC")

            # Auto-withdraw if there is profit
            if bal > 0 and auto_withdraw:
                print("💸 Withdrawing profits to owner...")
                wtx = arb_contract.functions.withdrawUSDC().transact({"from": owner})
                w3.eth.wait_for_transaction_receipt(wtx)
                print("✅ Withdrawn.")

            # Owner balance + profit
            end_bal_raw = usdc.functions.balanceOf(owner).call()
            profit_raw = end_bal_raw - start_bal_raw
            print(f"💼 OWNER BALANCE: {end_bal_raw / 1e6:.6f} USDC ({end_bal_raw} raw)")
            print(f"🤑 NET PROFIT: {profit_raw / 1e6:.6f} USDC ({profit_raw} raw)")
        else:
            print("❌ FAILED: Transaction Reverted.")

    except Exception as e:
        print(f"\n❌ EXECUTION ERROR: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Manual flash swap execution")
    parser.add_argument("--borrow", type=float, default=10.0, help="Amount of WETH to borrow")
    parser.add_argument("--no-withdraw", action="store_true", help="Do not auto-withdraw profits")
    args = parser.parse_args()
    execute(borrow_weth=args.borrow, auto_withdraw=not args.no_withdraw)
