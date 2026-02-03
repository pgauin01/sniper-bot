from web3 import Web3
import json

w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))

# Load Bot Address
try:
    with open("arb_deployment.json", "r") as f:
        data = json.load(f)
        arb_address = data["address"]
except Exception:
    print("❌ arb_deployment.json missing.")
    exit()

# Config
PAIR_ADDRESS = "0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc"
WETH = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"

print(f"--- 🏥 SYSTEM DIAGNOSTICS ---")

# 1. Check Bot Code
code = w3.eth.get_code(arb_address)
if code in (b"", b"\x00"):
    print(f"❌ BOT CRITICAL: Contract {arb_address} has NO CODE!")
    print("   -> Fix: You must run 'python scripts/deploy_arb.py' again.")
else:
    print(f"✅ BOT OK: Contract exists ({len(code)} bytes).")

# 2. Check Pair Code
code_pair = w3.eth.get_code(PAIR_ADDRESS)
if code_pair in (b"", b"\x00"):
    print(f"❌ PAIR CRITICAL: Uniswap Pair {PAIR_ADDRESS} has NO CODE!")
    print("   -> Fix: Restart Ganache with the correct --fork URL.")
else:
    print(f"✅ PAIR OK: Uniswap Pair exists.")

# 3. Check Reserves
try:
    pair_abi = [
        {
            "name": "getReserves",
            "inputs": [],
            "outputs": [
                {"name": "_reserve0", "type": "uint112"},
                {"name": "_reserve1", "type": "uint112"},
                {"name": "_blockTimestampLast", "type": "uint32"},
            ],
            "stateMutability": "view",
            "type": "function",
        }
    ]

    pair_contract = w3.eth.contract(address=PAIR_ADDRESS, abi=pair_abi)
    reserves = pair_contract.functions.getReserves().call()

    print(
        f"✅ RESERVES: Pair holds "
        f"{reserves[0] / 1e6:.2f} USDC and "
        f"{reserves[1] / 1e18:.2f} WETH"
    )
except Exception as e:
    print(f"❌ PAIR ERROR: Could not read reserves. {e}")

# 4. Check Bot Owner
try:
    bot_abi = [
        {
            "name": "owner",
            "inputs": [],
            "outputs": [{"name": "", "type": "address"}],
            "stateMutability": "view",
            "type": "function",
        }
    ]

    bot = w3.eth.contract(address=arb_address, abi=bot_abi)
    owner = bot.functions.owner().call()

    print(f"✅ OWNER CHECK: Bot Owner is {owner}")

    if owner != w3.eth.accounts[0]:
        print(
            f"⚠️ WARNING: Bot owner ({owner}) "
            f"!= Your Account ({w3.eth.accounts[0]})"
        )
    else:
        print("✅ Owner Match.")
except Exception as e:
    print(f"❌ OWNER ERROR: {e}")
