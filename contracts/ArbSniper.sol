// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

interface IUniswapV2Pair {
    function swap(uint amount0Out, uint amount1Out, address to, bytes calldata data) external;
}

contract ArbSniper is Ownable {
    address constant UNISWAP_ROUTER = 0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D;
    address constant SUSHISWAP_ROUTER = 0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F;
    address constant WETH = 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2;

    constructor() Ownable(msg.sender) {}

    // 1. TRIGGER: Start the Flash Loan
    function startFlashArbitrage(address tokenPair, uint amountToBorrow) external onlyOwner {
        bytes memory data = abi.encode(UNISWAP_ROUTER, SUSHISWAP_ROUTER);
        IUniswapV2Pair(tokenPair).swap(amountToBorrow, 0, address(this), data);
    }

    // 2. CALLBACK: Uniswap calls this after giving the loan
    function uniswapV2Call(address sender, uint amount0, uint amount1, bytes calldata data) external {
        require(amount0 > 0 || amount1 > 0, "No funds borrowed");
        uint amountReceived = amount0;

        // In a real bot, we would swap on SushiSwap here.
        // For this SIMULATION, we just approve and pay back to prove it works.
        
        // Repay Loan + 0.3% Fee
        uint fee = (amountReceived * 3) / 997 + 1;
        uint amountToRepay = amountReceived + fee;
        
        IERC20(WETH).transfer(msg.sender, amountToRepay);
    }
}