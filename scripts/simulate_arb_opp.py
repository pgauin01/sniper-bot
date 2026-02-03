import os
import time
from web3 import Web3

def load_env(path):
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ[key] = value

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_env(os.path.join(ROOT_DIR, ".env"))

# 1. Connect
RPC_URL = os.environ.get("WEB3_PROVIDER_URI", "http://127.0.0.1:8545")
w3 = Web3(Web3.HTTPProvider(RPC_URL))

# 2. Configuration
WETH = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
USDC = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
UNISWAP_ROUTER = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"
SUSHISWAP_ROUTER = "0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F"

WHALE = w3.to_checksum_address(
    os.environ.get("WHALE_ADDRESS", "0x0A59649758aa4d66E25f08Dd01dacb9202FB4700")
)
USDC_WHALE = w3.to_checksum_address(
    os.environ.get("USDC_WHALE", "0x203520F4ec42Ea39b03F62B20e20Cf17DB5fdfA7")
)
USDC_TRADE_AMOUNT = int(float(os.environ.get("USDC_TRADE_AMOUNT", "10000000")))
DEPLOYER = w3.eth.accounts[0]

# ABIs
router_abi = [
    {"name": "swapExactTokensForTokens", "inputs": [{"name": "amountIn", "type": "uint256"}, {"name": "amountOutMin", "type": "uint256"}, {"name": "path", "type": "address[]"}, {"name": "to", "type": "address"}, {"name": "deadline", "type": "uint256"}], "outputs": [{"name": "amounts", "type": "uint256[]"}], "stateMutability": "nonpayable", "type": "function"},
    {"name": "getAmountsOut", "inputs": [{"name": "amountIn", "type": "uint256"}, {"name": "path", "type": "address[]"}], "outputs": [{"name": "amounts", "type": "uint256[]"}], "stateMutability": "view", "type": "function"}
]
erc20_abi = [
    {"name": "approve", "inputs": [{"name": "spender", "type": "address"}, {"name": "amount", "type": "uint256"}], "outputs": [{"name": "", "type": "bool"}], "type": "function"},
    {"name": "balanceOf", "inputs": [{"name": "account", "type": "address"}], "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"name": "transfer", "inputs": [{"name": "recipient", "type": "address"}, {"name": "amount", "type": "uint256"}], "outputs": [{"name": "", "type": "bool"}], "type": "function"}
]

uniswap = w3.eth.contract(address=UNISWAP_ROUTER, abi=router_abi)
sushi = w3.eth.contract(address=SUSHISWAP_ROUTER, abi=router_abi)
usdc_token = w3.eth.contract(address=USDC, abi=erc20_abi)

print(f"RPC: {RPC_URL}")
print(f"USDC Whale: {USDC_WHALE}")
print(f"USDC Trade Amount: ${USDC_TRADE_AMOUNT:,.0f}")

print(f"--- 📉 MANIPULATING MARKET (MAINNET FORK) ---")
print(f"Whale Address: {WHALE}")

# --- STEP 1: FUND THE WHALE WITH ETH ---
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
print("\n💥 Whale is buying $10,000,000 worth of WETH on Uniswap...")

try:
    # Check USDC Balance
    usdc_bal = usdc_token.functions.balanceOf(WHALE).call()
    print(f"Whale USDC Balance: ${usdc_bal / 1e6:,.2f}")
    usdc_whale_bal = usdc_token.functions.balanceOf(USDC_WHALE).call()
    print(f"USDC Whale Balance: ${usdc_whale_bal / 1e6:,.2f}")

    trade_amount = USDC_TRADE_AMOUNT * 10**6

    if usdc_bal < trade_amount:
        required = trade_amount - usdc_bal
        if usdc_whale_bal < required:
            print("Error: USDC_WHALE does not have enough balance for this trade.")
            print("Set USDC_WHALE to a richer holder or lower USDC_TRADE_AMOUNT.")
            exit()

        print("Whale needs USDC. Funding from USDC whale...")
        usdc_token.functions.transfer(
            WHALE,
            required
        ).transact({"from": USDC_WHALE})

        usdc_bal = usdc_token.functions.balanceOf(WHALE).call()
        print(f"Whale USDC Balance (after funding): ${usdc_bal / 1e6:,.2f}")
        if usdc_bal < trade_amount:
            print("Error: Whale still underfunded. Check USDC_WHALE unlock.")
            exit()

    # Approve
    usdc_token.functions.approve(UNISWAP_ROUTER, 2**256 - 1).transact({"from": WHALE})

    # Swap
    tx_hash = uniswap.functions.swapExactTokensForTokens(
        trade_amount, 
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
