import time
import json
import os
from web3 import Web3

# 1. Connect via WebSocket (Faster!)
# Note: Ganache CLI supports WS on the same port by default
try:
    w3 = Web3(Web3.WebsocketProvider("ws://127.0.0.1:8545"))
    if w3.is_connected():
        print("✅ Connected via WebSockets (wss://) - High Speed Mode")
    else:
        raise Exception("WS Connection failed")
except:
    print("⚠️ WS failed, falling back to HTTP...")
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
bought_tokens = set()

# Load Memory
if os.path.exists("sniped_tokens.txt"):
    with open("sniped_tokens.txt", "r") as f:
        for line in f:
            clean_addr = line.strip()
            if clean_addr:
                bought_tokens.add(clean_addr)
    print(f"🧠 Memory Loaded: {len(bought_tokens)} tokens ignored.")

# --- NEW: HONEYPOT CHECK FUNCTION ---
def is_safe_token(token_address):
    print(f"   🛡️ Running Honeypot Simulation on {token_address}...")
    try:
        # We simulate a small trade (0.1 ETH)
        # .call() runs it locally without spending gas
        sniper.functions.checkHoneypot(token_address).call({
            "from": owner, 
            "value": w3.to_wei(0.1, 'ether')
        })
        print("   ✅ Simulation Passed: Token is Buyable & Sellable.")
        return True
    except Exception as e:
        print(f"   ❌ HONEYPOT DETECTED! Simulation reverted.")
        # print(f"      Reason: {e}") # Uncomment to see full error
        return False
# ------------------------------------

def handle_event(tx, tx_input_str):
    try:
        token_address_hex = "0x" + tx_input_str[34:74]
        token_address = w3.to_checksum_address(token_address_hex)
        
        if token_address in bought_tokens:
            print(f"\n⚠️ Ignored Duplicate Token: {token_address}")
            return False
        
        print(f"\n🚨 LIQUIDITY DETECTED! Token: {token_address}")
        
        # --- EXECUTE HONEYPOT CHECK ---
        if not is_safe_token(token_address):
            print("⛔ ABORTING SNIPE: Token is unsafe.")
            return False
        # ------------------------------

        print("🔫 FIRING SNIPE TRANSACTION...")
        snipe_tx = sniper.functions.snipe(token_address, 0).transact({
            "from": owner,
            "value": w3.to_wei(0.1, 'ether'), 
            "gas": 500000
        })
        print(f"✅ Snipe Sent! Tx: {snipe_tx.hex()}")

        with open("sniped_tokens.txt", "a") as f:
            f.write(token_address + "\n")
        bought_tokens.add(token_address)
        print(f"💾 Saved {token_address} to database.")

        # --- NEW: SMART SELL LOGIC ---
        print("📉 Entering Position Manager (Take Profit: +20% | Stop Loss: -10%)")
        
        # 1. Get Token Balance
        time.sleep(2) # Wait for buy to confirm
        token_balance = sniper.functions.getTokenBalance(token_address).call()
        if token_balance == 0:
            print("❌ Error: Zero tokens found. Buy might have failed.")
            return False

        # 2. Monitor Price Loop
        initial_eth_value = w3.to_wei(0.1, 'ether') # What we spent
        target_value = initial_eth_value * 1.2      # +20%
        stop_loss_value = initial_eth_value * 0.9   # -10%
        
        start_time = time.time()
        while True:
            try:
                # Ask Router: "How much ETH if I sell now?"
                # Path: Token -> WETH
                amounts = sniper.functions.getAmountsOut(token_address, token_balance).call()
                current_eth_value = amounts[1]
                
                # Calculate PnL Percentage
                pnl_percent = ((current_eth_value - initial_eth_value) / initial_eth_value) * 100
                
                print(f"   📊 Current Value: {w3.from_wei(current_eth_value, 'ether'):.4f} ETH ({pnl_percent:+.2f}%)")
                
                # CHECK TARGETS
                if current_eth_value >= target_value:
                    print("🚀 TARGET HIT! Taking Profit...")
                    break # Break loop to sell
                
                if current_eth_value <= stop_loss_value:
                    print("🔻 STOP LOSS HIT! Bailing out...")
                    break # Break loop to sell
                
                # Timeout (Optional: Sell anyway after 60 seconds)
                if time.time() - start_time > 60:
                    print("⏰ Timeout reached. Selling now.")
                    break
                    
                time.sleep(1)
                
            except Exception as e:
                print(f"   ⚠️ Error checking price: {e}")
                time.sleep(1)

        print("💰 EXECUTING SELL...")
        try:
            sell_tx = sniper.functions.sell(token_address).transact({
                "from": owner,
                "gas": 500000
            })
            print(f"✅ Sold Successfully! Tx: {sell_tx.hex()}")
        except Exception as e:
            print(f"❌ Sell Failed: {e}")
        # ----------------------------

        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def scan_block(block_number):
    # print(f"   Scanning {block_number}...") # Quiet mode for speed
    try:
        block = w3.eth.get_block(block_number, full_transactions=True)
        for tx in block.transactions:
            tx_hash = tx['hash'].hex()
            if tx_hash in processed_txs:
                continue

            if tx['to'] and tx['to'].lower() == ROUTER_ADDRESS:
                tx_input_str = tx['input'].hex()
                if not tx_input_str.startswith("0x"):
                    tx_input_str = "0x" + tx_input_str
                
                if tx_input_str.startswith(TARGET_METHOD_ID):
                    handle_event(tx, tx_input_str)
            
            processed_txs.add(tx_hash)
    except Exception as e:
        print(f"Error block {block_number}: {e}")

# --- MAIN EXECUTION ---
print("--- 🦅 SNIPER BOT v2 (WS + ANTI-HONEYPOT) ---")

current_block = w3.eth.block_number
print(f"🔍 Current Block: {current_block}. Catching up...")

for b in range(max(0, current_block - 5), current_block + 1):
    scan_block(b)

print("\n👀 Live Watcher Active...")
while True:
    try:
        latest_block = w3.eth.block_number
        while current_block < latest_block:
            current_block += 1
            scan_block(current_block)
        time.sleep(0.5) # Faster polling
    except KeyboardInterrupt:
        print("Stopping...")
        break