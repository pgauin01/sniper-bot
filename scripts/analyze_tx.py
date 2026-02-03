from web3 import Web3
import json

w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))

# --- CONFIGURATION ---
# The successful hash you just got
TX_HASH = "0x2ef5fd45d9ef2efb6c88f540dda2501b75389aa54052cc58a02a561907492252"

WETH = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
USDC = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"

# Load Contract
try:
    with open("arb_deployment.json", "r") as f:
        data = json.load(f)
        arb_address = data["address"]
except:
    print("❌ JSON file not found")
    exit()

print(f"--- 🕵️‍♂️ TRANSACTION AUTOPSY ---")
print(f"Tx Hash: {TX_HASH[:12]}...")
print(f"Contract: {arb_address}")

# Get Receipt
try:
    receipt = w3.eth.get_transaction_receipt(TX_HASH)
    print(f"Status: {'✅ SUCCESS' if receipt.status == 1 else '❌ FAILED'}")
    print(f"Block: {receipt.blockNumber}")
except Exception as e:
    print(f"❌ Could not find Tx: {e}")
    exit()

# ERC20 Transfer Event Signature
TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"

logs = receipt['logs']
print(f"\n📄 Token Movements ({len(logs)} Events):")

for i, log in enumerate(logs):
    if len(log['topics']) > 0 and log['topics'][0].hex() == TRANSFER_TOPIC:
        # Decode Addresses
        from_addr = w3.to_checksum_address("0x" + log['topics'][1].hex()[-40:])
        to_addr = w3.to_checksum_address("0x" + log['topics'][2].hex()[-40:])
        amount = int(log['data'].hex(), 16)
        
        # Identify Token
        token_name = "UNKNOWN"
        decimals = 18
        if log['address'] == WETH: 
            token_name = "WETH"
            decimals = 18
        elif log['address'] == USDC: 
            token_name = "USDC"
            decimals = 6
        
        readable_amount = amount / (10 ** decimals)
        
        # Highlight our contract
        prefix = "  "
        if to_addr == arb_address: prefix = "🟢 IN "
        if from_addr == arb_address: prefix = "🔴 OUT"
        
        print(f"{prefix} {readable_amount:,.2f} {token_name} | {from_addr[:6]}... -> {to_addr[:6]}...")

print("\n--- 💰 CURRENT HOLDINGS CHECK ---")
erc20_abi = [{"name": "balanceOf", "inputs": [{"name": "account", "type": "address"}], "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"}]

weth_contract = w3.eth.contract(address=WETH, abi=erc20_abi)
usdc_contract = w3.eth.contract(address=USDC, abi=erc20_abi)

weth_bal = weth_contract.functions.balanceOf(arb_address).call() / 1e18
usdc_bal = usdc_contract.functions.balanceOf(arb_address).call() / 1e6

print(f"WETH Balance: {weth_bal:,.4f}")
print(f"USDC Balance: {usdc_bal:,.2f}")