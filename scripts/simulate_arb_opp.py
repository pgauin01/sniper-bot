import time
from web3 import Web3

# 1. Connect
w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))

# 2. Configuration
WETH = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
USDC = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
UNISWAP_ROUTER = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"
SUSHISWAP_ROUTER = "0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F"

# --- USE THE WHALE THAT HAS MONEY ---
WHALE = w3.to_checksum_address("0x46340b20830761efd32832A74d7169B29FEB9758")
DEPLOYER = w3.eth.accounts[0]

# ABIs
router_abi = [
    {"name": "swapExactTokensForTokens", "inputs": [{"name": "amountIn", "type": "uint256"}, {"name": "amountOutMin", "type": "uint256"}, {"name": "path", "type": "address[]"}, {"name": "to", "type": "address"}, {"name": "deadline", "type": "uint256"}], "outputs": [{"name": "amounts", "type": "uint256[]"}], "stateMutability": "nonpayable", "type": "function"},
    {"name": "getAmountsOut", "inputs": [{"name": "amountIn", "type": "uint256"}, {"name": "path", "type": "address[]"}], "outputs": [{"name": "amounts", "type": "uint256[]"}], "stateMutability": "view", "type": "function"}
]
erc20_abi = [
    {"name": "approve", "inputs": [{"name": "spender", "type": "address"}, {"name": "amount", "type": "uint256"}], "outputs": [{"name": "", "type": "bool"}], "type": "function"},
    {"name": "balanceOf", "inputs": [{"name": "account", "type": "address"}], "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
]

uniswap = w3.eth.contract(address=UNISWAP_ROUTER, abi=router_abi)
sushi = w3.eth.contract(address=SUSHISWAP_ROUTER, abi=router_abi)
usdc_token = w3.eth.contract(address=USDC, abi=erc20_abi)

print(f"--- 📉 MANIPULATING MARKET (MAINNET FORK) ---")
print(f"Whale Address: {WHALE}")

# --- STEP 1: FUND GAS (ETH) ---
whale_eth = w3.eth.get_balance(WHALE)
print(f"🐳 Whale ETH Balance: {w3.from_wei(whale_eth, 'ether'):.4f} ETH")

if whale_eth < w3.to_wei(1, 'ether'):
    print("⚠️ Whale needs gas. Sending 10 ETH...")
    w3.eth.send_transaction({
        'to': WHALE,
        'from': DEPLOYER,
        'value': w3.to_wei(10, 'ether')
    })
    print("✅ Gas Sent.")

# --- STEP 2: EXECUTE DUMP ---
print("\n💥 Whale is buying USDC -> WETH on Uniswap...")

try:
    # Check USDC Balance
    usdc_bal = usdc_token.functions.balanceOf(WHALE).call()
    print(f"💰 Whale USDC Balance: ${usdc_bal / 1e6:,.2f}")
    DESIRED_TRADE = 9_000_000 * 10**6
    AMOUNT_TO_TRADE = min(DESIRED_TRADE, int(usdc_bal * 0.95))

    if AMOUNT_TO_TRADE <= 0:
        print("??? Error: Whale has no USDC to trade.")
        exit()

    print(f"Using trade amount: ${AMOUNT_TO_TRADE / 1e6:,.2f} USDC")


    # Approve
    usdc_token.functions.approve(UNISWAP_ROUTER, 2**256 - 1).transact({"from": WHALE})

    # Swap
    tx_hash = uniswap.functions.swapExactTokensForTokens(
        AMOUNT_TO_TRADE,  # <--- Update this variable usage too
        0,
        [USDC, WETH],
        WHALE,
        int(time.time()) + 120
    ).transact({
        "from": WHALE,
        "gas": 300000
    })
    
    print("✅ Trade Submitted. Waiting for receipt...")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    if receipt.status == 1:
        print("✅ Trade Successful! Price Gap Created.")
    else:
        print("❌ Trade REVERTED!")

except Exception as e:
    print(f"❌ Execution Failed: {e}")

# --- STEP 3: CHECK PRICES ---
amount_in = w3.to_wei(1, 'ether')
uni_price = uniswap.functions.getAmountsOut(amount_in, [WETH, USDC]).call()[1] / 1e6
sushi_price = sushi.functions.getAmountsOut(amount_in, [WETH, USDC]).call()[1] / 1e6

print(f"\nAFTER:")
print(f"   Uniswap Price:   ${uni_price:.2f}")
print(f"   SushiSwap Price: ${sushi_price:.2f}")

diff = uni_price - sushi_price
print(f"✅ GAP CREATED: ${diff:.2f} difference per ETH")