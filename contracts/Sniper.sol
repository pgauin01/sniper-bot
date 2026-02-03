// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

interface IUniswapV2Router {
    function swapExactETHForTokens(
        uint amountOutMin, 
        address[] calldata path, 
        address to, 
        uint deadline
    ) external payable returns (uint[] memory amounts);

    function swapExactTokensForETHSupportingFeeOnTransferTokens(
        uint amountIn,
        uint amountOutMin,
        address[] calldata path,
        address to,
        uint deadline
    ) external;

    function getAmountsOut(uint amountIn, address[] calldata path) external view returns (uint[] memory amounts);
}

contract Sniper is Ownable {
    address constant ROUTER = 0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D;
    address constant WETH = 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2;

    constructor() Ownable(msg.sender) {}

    // ▼▼▼ THIS IS THE CRITICAL MISSING LINE ▼▼▼
    receive() external payable {}
    // ▲▲▲ WITHOUT THIS, SELLING FAILS ▲▲▲

    function snipe(address tokenAddress, uint amountOutMin) external payable onlyOwner {
        address[] memory path = new address[](2);
        path[0] = WETH;
        path[1] = tokenAddress;

        IUniswapV2Router(ROUTER).swapExactETHForTokens{value: msg.value}(
            amountOutMin,
            path,
            address(this),
            block.timestamp + 1200
        );
    }

    function checkHoneypot(address tokenAddress) external payable onlyOwner returns (bool) {
        address[] memory buyPath = new address[](2);
        buyPath[0] = WETH;
        buyPath[1] = tokenAddress;

        // 1. Simulate Buy
        uint[] memory amounts = IUniswapV2Router(ROUTER).swapExactETHForTokens{value: msg.value}(
            0, buyPath, address(this), block.timestamp + 120
        );
        uint tokenAmount = amounts[1];

        // 2. Approve
        IERC20(tokenAddress).approve(ROUTER, tokenAmount);

        // 3. Simulate Sell
        address[] memory sellPath = new address[](2);
        sellPath[0] = tokenAddress;
        sellPath[1] = WETH;

        try IUniswapV2Router(ROUTER).swapExactTokensForETHSupportingFeeOnTransferTokens(
            tokenAmount, 
            0, 
            sellPath, 
            address(this), 
            block.timestamp + 120
        ) {
            return true;
        } catch {
            revert("Honeypot detected: Sell failed");
        }
    }
    
    function withdrawETH() external onlyOwner {
        payable(owner()).transfer(address(this).balance);
    }

    function sell(address tokenAddress) external onlyOwner {
        // 1. Check Balance
        uint256 balance = IERC20(tokenAddress).balanceOf(address(this));
        require(balance > 0, "No tokens to sell");

        // 2. Approve Router
        IERC20(tokenAddress).approve(ROUTER, balance);

        // 3. Define Path (Token -> WETH)
        address[] memory path = new address[](2);
        path[0] = tokenAddress;
        path[1] = WETH;

        // 4. Execute Swap
        // We accept any amount of ETH (amountOutMin = 0) for speed in this demo
        IUniswapV2Router(ROUTER).swapExactTokensForETHSupportingFeeOnTransferTokens(
            balance,
            0,
            path,
            address(this),
            block.timestamp + 120
        );
    }

    // Helper: Check how many tokens the contract holds
    function getTokenBalance(address tokenAddress) external view returns (uint256) {
        return IERC20(tokenAddress).balanceOf(address(this));
    }

    // Helper: Check the current ETH value of those tokens
    function getAmountsOut(address tokenAddress, uint256 amountIn) external view returns (uint[] memory amounts) {
        address[] memory path = new address[](2);
        path[0] = tokenAddress;
        path[1] = WETH;
        return IUniswapV2Router(ROUTER).getAmountsOut(amountIn, path);
    }
}