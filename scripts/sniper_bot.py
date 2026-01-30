import time
import json
from web3 import Web3

w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))

# Load your deployed Sniper Contract
with open("sniper_deployment.json", "r") as f:
    data = json.load(f)
    sniper_address = data["address"]
    sniper_abi = data["abi"]

sniper = w3.eth.contract(address=sniper_address, abi=sniper_abi)
owner = w3.eth.accounts[0]

print("--- 🦅 SNIPER BOT ACTIVATED ---")
print("Scanning Mempool for 'addLiquidityETH'...")

# The "fingerprint" of the addLiquidityETH function
TARGET_METHOD_ID = "0xf305d719" 
# Target Router (We convert to lowercase for safe comparison)
ROUTER_ADDRESS = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D".lower()

def handle_event(tx, tx_input_str):
    try:
        # Decode Token Address from Input Data
        token_address_hex = "0x" + tx_input_str[34:74]
        token_address = w3.to_checksum_address(token_address_hex)
        
        print(f"\n🚨 LIQUIDITY DETECTED! Token: {token_address}")
        print(f"   Target Tx: {tx['hash'].hex()}")
        
        print("🔫 FIRING SNIPE TRANSACTION...")
        snipe_tx = sniper.functions.snipe(
            token_address,
            0 
        ).transact({
            "from": owner,
            "value": w3.to_wei(0.1, 'ether'), 
            "gas": 400000
        })
        
        print(f"✅ Snipe Sent! Tx: {snipe_tx.hex()}")
        return True
    except Exception as e:
        print(f"❌ Error decoding/sniping: {e}")
        return False

processed_txs = set()

while True:
    try:
        block = w3.eth.get_block('latest', full_transactions=True)
        
        for tx in block.transactions:
            tx_hash = tx['hash'].hex()
            if tx_hash in processed_txs:
                continue
            
            # --- FIX: Case-Insensitive Check ---
            # We convert the tx['to'] to lowercase before comparing
            if tx['to'] and tx['to'].lower() == ROUTER_ADDRESS:
                
                # Convert input bytes to hex string
                tx_input_str = tx['input'].hex()
                
                if tx_input_str.startswith(TARGET_METHOD_ID):
                    if handle_event(tx, tx_input_str):
                        exit() 
            
            processed_txs.add(tx_hash)
        
        time.sleep(1)
        
    except KeyboardInterrupt:
        print("Stopping Bot...")
        break
    except Exception as e:
        print(f"Loop Error: {e}")
        time.sleep(1)