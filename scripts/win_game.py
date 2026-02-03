import time
from web3 import Web3
from solcx import compile_standard, install_solc

# --- CONTRACT (Proven Logic) ---
SOLIDITY_CODE = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

interface IERC20 {
    function balanceOf(address account) external view returns (uint256);
    function transfer(address recipient, uint256 amount) external returns (bool);
    function approve(address spender, uint256 amount) external returns (bool);
}

interface IUniswapV2Pair {
    function swap(uint amount0Out, uint amount1Out, address to, bytes calldata data) external;
    function token0() external view returns (address);
    function getReserves() external view returns (uint112 reserve0, uint112 reserve1, uint32 blockTimestampLast);
}

interface IUniswapV2Router {
    function swapExactTokensForTokens(
        uint amountIn, uint amountOutMin, address[] calldata path, address to, uint deadline
    ) external returns (uint[] memory amounts);
}

contract ArbWinner {
    address constant UNISWAP_ROUTER = 0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D;
    address constant WETH = 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2;
    address constant USDC = 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48;
    
    address private owner;
    event ArbResult(uint wethBorrowed, uint usdcReceived, uint amountToRepay);
    
    constructor() { owner = msg.sender; }

    function startFlashArbitrage(address pairAddress, uint amountWethToBorrow) external {
        require(msg.sender == owner, "Only Owner");
        bytes memory data = abi.encode(pairAddress);
        address token0 = IUniswapV2Pair(pairAddress).token0();
        uint amount0Out = token0 == WETH ? amountWethToBorrow : 0;
        uint amount1Out = token0 == WETH ? 0 : amountWethToBorrow;
        IUniswapV2Pair(pairAddress).swap(amount0Out, amount1Out, address(this), data);
    }

    function uniswapV2Call(address sender, uint amount0, uint amount1, bytes calldata data) external {
        uint wethBorrowed = amount0 == 0 ? amount1 : amount0;
        IERC20(WETH).approve(UNISWAP_ROUTER, wethBorrowed);
        address[] memory path = new address[](2);
        path[0] = WETH;
        path[1] = USDC;
        uint[] memory amounts = IUniswapV2Router(UNISWAP_ROUTER).swapExactTokensForTokens(
            wethBorrowed, 0, path, address(this), block.timestamp + 60
        );
        uint usdcReceived = amounts[1];
        
        address pair = msg.sender;
        (uint112 reserve0, uint112 reserve1,) = IUniswapV2Pair(pair).getReserves();
        address token0 = IUniswapV2Pair(pair).token0();
        (uint reserveIn, uint reserveOut) = token0 == USDC ? (uint(reserve0), uint(reserve1)) : (uint(reserve1), uint(reserve0));

        uint numerator = wethBorrowed * reserveIn * 1000;
        uint denominator = (reserveOut - wethBorrowed) * 997;
        uint amountToRepay = (numerator / denominator) + 1;

        emit ArbResult(wethBorrowed, usdcReceived, amountToRepay);
        require(usdcReceived > amountToRepay, "Not enough profit to repay loan!");
        IERC20(USDC).transfer(pair, amountToRepay);
    }
    
    function withdrawUSDC() external {
        uint balance = IERC20(USDC).balanceOf(address(this));
        IERC20(USDC).transfer(owner, balance);
    }
}
"""

def main():
    w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
    owner = w3.eth.accounts[0]
    USDC = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
    WETH = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
    
    usdc_contract = w3.eth.contract(address=USDC, abi=[{"name": "balanceOf", "inputs": [{"name": "account", "type": "address"}], "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"}])
    
    print("--- 🏁 STARTING ULTIMATE HEIST ---")
    
    # 0. INITIAL CHECK
    start_bal = usdc_contract.functions.balanceOf(owner).call() / 1e6
    print(f"💼 Owner Start Balance: ${start_bal:,.2f}")

    # 1. DEPLOY
    print("🔨 Compiling & Deploying...")
    install_solc("0.8.0")
    compiled = compile_standard({
        "language": "Solidity",
        "sources": {"ArbWinner.sol": {"content": SOLIDITY_CODE}},
        "settings": {"outputSelection": {"*": {"*": ["abi", "evm.bytecode"]}}}
    }, solc_version="0.8.0")
    
    abi = compiled["contracts"]["ArbWinner.sol"]["ArbWinner"]["abi"]
    bytecode = compiled["contracts"]["ArbWinner.sol"]["ArbWinner"]["evm"]["bytecode"]["object"]
    
    ArbWinner = w3.eth.contract(abi=abi, bytecode=bytecode)
    tx = ArbWinner.constructor().transact({"from": owner})
    receipt = w3.eth.wait_for_transaction_receipt(tx)
    bot_addr = receipt.contractAddress
    bot = w3.eth.contract(address=bot_addr, abi=abi)
    print(f"✅ Bot Ready: {bot_addr}")

    # 2. CREATE GAP
    print("\n📉 Creating Market Gap...")
    WHALE = w3.to_checksum_address("0x46340b20830761efd32832A74d7169B29FEB9758")
    UNISWAP_ROUTER = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"
    
    usdc_erc20 = w3.eth.contract(address=USDC, abi=[{"name": "approve", "inputs": [{"name": "spender", "type": "address"}, {"name": "amount", "type": "uint256"}], "outputs": [{"name": "", "type": "bool"}], "type": "function"}])
    uniswap = w3.eth.contract(address=UNISWAP_ROUTER, abi=[
        {"name": "swapExactTokensForTokens", "inputs": [{"name": "amountIn", "type": "uint256"}, {"name": "amountOutMin", "type": "uint256"}, {"name": "path", "type": "address[]"}, {"name": "to", "type": "address"}, {"name": "deadline", "type": "uint256"}], "outputs": [{"name": "amounts", "type": "uint256[]"}], "stateMutability": "nonpayable", "type": "function"},
        {"name": "getAmountsOut", "inputs": [{"name": "amountIn", "type": "uint256"}, {"name": "path", "type": "address[]"}], "outputs": [{"name": "amounts", "type": "uint256[]"}], "stateMutability": "view", "type": "function"}
    ])
    
    usdc_erc20.functions.approve(UNISWAP_ROUTER, 2**256-1).transact({"from": WHALE})
    tx = uniswap.functions.swapExactTokensForTokens(
        9_000_000 * 10**6, 0, [USDC, WETH], WHALE, int(time.time())+120
    ).transact({"from": WHALE, "gas": 300000})
    w3.eth.wait_for_transaction_receipt(tx)
    
    # Check Price
    price = uniswap.functions.getAmountsOut(w3.to_wei(1, 'ether'), [WETH, USDC]).call()[1] / 1e6
    print(f"✅ Gap Created. Uniswap Price: ${price:,.2f}")

    # 2b. PAIR SANITY CHECK
    SUSHI_FACTORY = w3.to_checksum_address("0xC0AEe478e3658e2610c5F7A4A2E1777cE9e4f2Ac")
    factory_abi = [
        {"name": "getPair", "inputs": [{"name": "tokenA", "type": "address"}, {"name": "tokenB", "type": "address"}], "outputs": [{"name": "pair", "type": "address"}], "stateMutability": "view", "type": "function"}
    ]
    factory_code = w3.eth.get_code(SUSHI_FACTORY)
    if factory_code in (b"", b"\x00"):
        print("\nPAIR CHECK:")
        print(f"factory address: {SUSHI_FACTORY}")
        print("SUSHI FACTORY NOT DEPLOYED ON THIS CHAIN. Aborting before flash swap.")
        return

    factory = w3.eth.contract(address=SUSHI_FACTORY, abi=factory_abi)
    pair_addr = factory.functions.getPair(WETH, USDC).call()
    if int(pair_addr, 16) == 0:
        print("\nPAIR CHECK:")
        print("NO SUSHI WETH/USDC PAIR FOUND. Aborting before flash swap.")
        return

    pair_abi = [
        {"name": "token0", "inputs": [], "outputs": [{"name": "", "type": "address"}], "stateMutability": "view", "type": "function"},
        {"name": "token1", "inputs": [], "outputs": [{"name": "", "type": "address"}], "stateMutability": "view", "type": "function"},
        {"name": "getReserves", "inputs": [], "outputs": [
            {"name": "reserve0", "type": "uint112"},
            {"name": "reserve1", "type": "uint112"},
            {"name": "blockTimestampLast", "type": "uint32"}
        ], "stateMutability": "view", "type": "function"}
    ]
    pair_code = w3.eth.get_code(pair_addr)
    if pair_code in (b"", b"\x00"):
        print("\nPAIR CHECK:")
        print(f"pair address: {pair_addr}")
        print("PAIR NOT DEPLOYED ON THIS CHAIN. Aborting before flash swap.")
        return

    pair = w3.eth.contract(address=pair_addr, abi=pair_abi)
    try:
        token0 = pair.functions.token0().call()
        token1 = pair.functions.token1().call()
        reserves = pair.functions.getReserves().call()
    except Exception as e:
        print("\nPAIR CHECK:")
        print(f"pair address: {pair_addr}")
        print(f"PAIR CALL FAILED: {e}")
        return
    is_weth_usdc = set([token0.lower(), token1.lower()]) == set([WETH.lower(), USDC.lower()])
    print("\nPAIR CHECK:")
    print(f"token0: {token0}")
    print(f"token1: {token1}")
    print(f"reserves: {reserves}")
    print(f"is_weth_usdc_pair: {is_weth_usdc}")
    if not is_weth_usdc:
        print("PAIR MISMATCH: Expected WETH/USDC. Aborting before flash swap.")
        return

    # 3. EXECUTE
    print("\nExecuting Flash Swap...")
    SUSHI_PAIR = pair_addr
    tx = bot.functions.startFlashArbitrage(SUSHI_PAIR, w3.to_wei(10, 'ether')).transact({"from": owner, "gas": 1000000})
    receipt = w3.eth.wait_for_transaction_receipt(tx)
    print("Trade Confirmed.")

    # 3b. LOGS
    try:
        for log in receipt["logs"]:
            if log["address"].lower() != bot_addr.lower():
                continue
            ev = bot.events.ArbResult().process_log(log)
            args = ev["args"]
            weth_borrowed = args["wethBorrowed"] / 1e18
            usdc_received = args["usdcReceived"] / 1e6
            repay = args["amountToRepay"] / 1e6
            print(f"ArbResult: borrowed {weth_borrowed:.6f} WETH, received {usdc_received:.6f} USDC, repay {repay:.6f} USDC")
    except Exception as e:
        print(f"Event decode skipped: {e}")

    # 4. ACCOUNTING CHECK
    print("\n--- ACCOUNTING CHECK ---")
    bot_bal_raw = usdc_contract.functions.balanceOf(bot_addr).call()
    bot_bal = bot_bal_raw / 1e6
    print(f"Bot Balance:   {bot_bal:.6f} USDC ({bot_bal_raw} raw)")
    
    if bot_bal_raw > 0:
        print("PROFIT FOUND IN BOT! Withdrawing...")
        bot.functions.withdrawUSDC().transact({"from": owner})
        print("Withdrawn.")
    else:
        print("Bot Empty. Checking Owner Wallet...")

    final_bal_raw = usdc_contract.functions.balanceOf(owner).call()
    final_bal = final_bal_raw / 1e6
    profit_raw = final_bal_raw - int(start_bal * 1e6)
    profit = profit_raw / 1e6
    print(f"Owner New Balance: {final_bal:.6f} USDC ({final_bal_raw} raw)")
    print(f"NET PROFIT: {profit:.6f} USDC ({profit_raw} raw)")

if __name__ == "__main__":
    main()
