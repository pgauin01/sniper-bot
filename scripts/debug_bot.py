import time
import json
from web3 import Web3

# 1. Connect
w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))

# 2. Load Config
with open("sniper_deployment.json", "r") as f:
    data = json.load(f)
    sniper_address = data["address"]
    sniper_abi = data["abi"]

sniper = w3.eth.contract(address=sniper_address, abi=sniper_abi)
owner = w3.eth.accounts[0]

# Config
TARGET_METHOD_ID = "0xf305d719" 
ROUTER_ADDRESS = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D".lower()
processed_txs = set()

def handle_event(tx, tx_input_str):
    try:
        # Debug print
        print(f"   >>> ATTEMPTING DECODE on Tx: {tx['hash'].hex()}")
        
        token_address_hex = "0x" + tx_input_str[34:74]
        token_address = w3.to_checksum_address(token_address_hex)
        
        print(f"\n🚨 LIQUIDITY DETECTED! Token: {token_address}")
        
        snipe_tx = sniper.functions.snipe(token_address, 0).transact({
            "from": owner,
            "value": w3.to_wei(0.1, 'ether'), 
            "gas": 500000
        })
        
        print(f"✅ Snipe Sent! Tx: {snipe_tx.hex()}")
        return True
    except Exception as e:
        print(f"❌ Error decoding/sniping: {e}")
        return False

def scan_block(block_number):
    print(f"   Scanning Block {block_number}...")
    try:
        block = w3.eth.get_block(block_number, full_transactions=True)
        
        for tx in block.transactions:
            tx_hash = tx['hash'].hex()
            
            # --- DEBUGGING LOGS ---
            # Check if this is the Liquidity Tx you just made?
            # (Optional: You can paste your specific tx hash here to filter)
            
            to_addr = tx['to']
            if to_addr:
                to_addr = to_addr.lower()
                
                # Check if it interacts with Router
                if to_addr == ROUTER_ADDRESS:
                    print(f"   🔍 Found Router Interaction: {tx_hash}")
                    
                    tx_input_str = tx['input'].hex()
                    method_id = tx_input_str[:10]
                    
                    print(f"      Method ID Found: {method_id}")
                    print(f"      Target ID Expected: {TARGET_METHOD_ID}")
                    
                    if tx_input_str.startswith(TARGET_METHOD_ID):
                        print("      ✅ METHOD ID MATCH!")
                        if handle_event(tx, tx_input_str):
                            return True
                    else:
                        print("      ❌ Method ID mismatch (Ignored)")
            # ----------------------
            
            processed_txs.add(tx_hash)
    except Exception as e:
        print(f"Error scanning block {block_number}: {e}")
    return False

# --- MAIN EXECUTION ---
print("--- 🕵️‍♂️ DEBUG BOT ACTIVATED ---")

current_block = w3.eth.block_number
print(f"🔍 Current Block: {current_block}. Scanning last 5 blocks...")

# 1. History Scan (Only last 5 for debug)
for b in range(max(0, current_block - 5), current_block + 1):
    if scan_block(b):
        print("🎯 Sniped from History!")
        exit()

print("\n👀 Live Watcher...")
while True:
    try:
        latest_block = w3.eth.block_number
        while current_block < latest_block:
            current_block += 1
            if scan_block(current_block):
                exit()
        time.sleep(1)
    except KeyboardInterrupt:
        break