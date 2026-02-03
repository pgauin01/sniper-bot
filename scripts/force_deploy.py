import json
import os
from web3 import Web3
from solcx import compile_standard, install_solc

# 1. THE PROVEN "GOLDEN CODE" (Embedded directly in Python to avoid file errors)
SOLIDITY_CODE = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

interface IERC20 {
    function balanceOf(address account) external view returns (uint256);
    function transfer(address recipient, uint256 amount) external returns (bool);
    function approve(address spender, uint256 amount) external returns (bool);
}

abstract contract Context {
    function _msgSender() internal view virtual returns (address) { return msg.sender; }
}

abstract contract Ownable is Context {
    address private _owner;
    constructor(address initialOwner) { _owner = initialOwner; }
    function owner() public view virtual returns (address) { return _owner; }
    modifier onlyOwner() { require(owner() == _msgSender(), "Ownable: caller is not the owner"); _; }
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

contract ArbSniper is Ownable {
    address constant UNISWAP_ROUTER = 0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D;
    address constant WETH = 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2;
    address constant USDC = 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48;

    constructor() Ownable(msg.sender) {}

    function startFlashArbitrage(address pairAddress, uint amountWethToBorrow) external onlyOwner {
        bytes memory data = abi.encode(pairAddress);
        address token0 = IUniswapV2Pair(pairAddress).token0();
        uint amount0Out = token0 == WETH ? amountWethToBorrow : 0;
        uint amount1Out = token0 == WETH ? 0 : amountWethToBorrow;
        IUniswapV2Pair(pairAddress).swap(amount0Out, amount1Out, address(this), data);
    }

    function uniswapV2Call(address sender, uint amount0, uint amount1, bytes calldata data) external {
        uint wethBorrowed = amount0 == 0 ? amount1 : amount0;
        
        // 1. SELL HIGH
        IERC20(WETH).approve(UNISWAP_ROUTER, wethBorrowed);
        address[] memory path = new address[](2);
        path[0] = WETH;
        path[1] = USDC;
        uint[] memory amounts = IUniswapV2Router(UNISWAP_ROUTER).swapExactTokensForTokens(
            wethBorrowed, 0, path, address(this), block.timestamp + 60
        );
        uint usdcReceived = amounts[1];

        // 2. INTERNAL MATH (The Fix)
        address pair = msg.sender;
        (uint112 reserve0, uint112 reserve1,) = IUniswapV2Pair(pair).getReserves();
        address token0 = IUniswapV2Pair(pair).token0();
        (uint reserveIn, uint reserveOut) = token0 == USDC ? (uint(reserve0), uint(reserve1)) : (uint(reserve1), uint(reserve0));

        uint numerator = wethBorrowed * reserveIn * 1000;
        uint denominator = (reserveOut - wethBorrowed) * 997;
        uint amountToRepay = (numerator / denominator) + 1;

        require(usdcReceived > amountToRepay, "Not enough profit to repay loan!");

        // 3. REPAY
        IERC20(USDC).transfer(pair, amountToRepay);
    }
}
"""

def force_deploy():
    # 2. OVERWRITE THE FILE
    print("✍️  Overwriting ArbSniper.sol with CORRECT code...")
    with open("contracts/ArbSniper.sol", "w") as f:
        f.write(SOLIDITY_CODE)

    # 3. COMPILE & DEPLOY
    install_solc("0.8.0")
    w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
    
    compiled_sol = compile_standard({
        "language": "Solidity",
        "sources": {"ArbSniper.sol": {"content": SOLIDITY_CODE}},
        "settings": {"outputSelection": {"*": {"*": ["abi", "evm.bytecode"]}}}
    }, solc_version="0.8.0")

    bytecode = compiled_sol["contracts"]["ArbSniper.sol"]["ArbSniper"]["evm"]["bytecode"]["object"]
    abi = compiled_sol["contracts"]["ArbSniper.sol"]["ArbSniper"]["abi"]

    deployer = w3.eth.accounts[0]
    ArbSniper = w3.eth.contract(abi=abi, bytecode=bytecode)
    
    print("🚀 Deploying NEW Contract...")
    tx_hash = ArbSniper.constructor().transact({"from": deployer})
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    
    print(f"✅ DEPLOYED AT: {tx_receipt.contractAddress}")
    
    with open("arb_deployment.json", "w") as f:
        json.dump({"address": tx_receipt.contractAddress, "abi": abi}, f)

if __name__ == "__main__":
    force_deploy()