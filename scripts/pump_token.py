import time
import json
import os
from web3 import Web3

# 1. Connect
w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))

# 2. Config
# We use Account #1 (Index 1) as the "Whale" so it doesn't conflict with your Bot (Index 0)
whale_account = w3.eth.accounts[1]
router_address = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"

# 3. Get the Target (Last Sniped Token)
if not os.path.exists("sniped_tokens.txt"):
    print("❌ No tokens found in history. Run the bot first.")
    exit()

with open("sniped_tokens.txt", "r") as f:
    lines = f.readlines()
    if not lines:
        print("❌ Token file is empty.")
        exit()
    target_token = lines[-1].strip()

print(f"--- 🐋 WHALE BOT ACTIVATED ---")
print(f"Target: {target_token}")
print(f"Whale:  {whale_account}")

# 4. Uniswap Router Interface
router_abi = [
    {
        "name": "swapExactETHForTokens",
        "inputs": [
            {"name": "amountOutMin", "type": "uint256"},
            {"name": "path", "type": "address[]"},
            {"name": "to", "type": "address"},
            {"name": "deadline", "type": "uint256"}
        ],
        "outputs": [{"name": "amounts", "type": "uint256[]"}],
        "stateMutability": "payable",
        "type": "function"
    }
]

router = w3.eth.contract(address=router_address, abi=router_abi)
WETH = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"

# 5. EXECUTE PUMP
amount_to_pump = 2  # Buy with 20 ETH (Massive buy for a small pool)

print(f"\n🚀 PUMPING {amount_to_pump} ETH into the chart...")

try:
    tx = router.functions.swapExactETHForTokens(
        0, # Accept any amount of tokens (Slippage ignored for pump)
        [WETH, target_token],
        whale_account,
        int(time.time()) + 120
    ).transact({
        "from": whale_account,
        "value": w3.to_wei(amount_to_pump, 'ether'),
        "gas": 300000
    })
    
    print(f"✅ MOON MISSION SUCCESSFUL!")
    print(f"   Tx: {tx.hex()}")
    print("   Watch your Sniper Bot terminal... it should sell NOW.")

except Exception as e:
    print(f"❌ Pump Failed: {e}")