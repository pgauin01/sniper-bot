from web3 import Web3

w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))

# Check 1: Block Number
# If it's 0, you are NOT forked. If it's 19,000,000+, you are good.
print(f"🌍 Current Block: {w3.eth.block_number}")

# Check 2: Uniswap Router Code
router = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"
code_size = len(w3.eth.get_code(router))

if code_size > 0:
    print(f"✅ Uniswap Router FOUND! (Size: {code_size})")
    print("🚀 SYSTEM READY. You can deploy now.")
else:
    print("❌ Uniswap Router NOT FOUND.")
    print("⚠️  STOP. Do not deploy. Check your API Key URL.")