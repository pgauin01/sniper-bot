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
}

contract Sniper is Ownable {
    // 1. HARDCODED ADDRESS (No more constructor errors)
    // This is the Uniswap V2 Router on Mainnet
    address constant ROUTER = 0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D;

    constructor() Ownable(msg.sender) {}

    function snipe(address tokenAddress, uint amountOutMin) external payable onlyOwner {
        address WETH = 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2;
        
        address[] memory path = new address[](2);
        path[0] = WETH;
        path[1] = tokenAddress;

        // 2. Call the Hardcoded Router
        IUniswapV2Router(ROUTER).swapExactETHForTokens{value: msg.value}(
            amountOutMin,
            path,
            address(this),
            block.timestamp + 1200 // 20 minute buffer
        );
    }
    
    // Helper to get money out if it fails
    function withdrawETH() external onlyOwner {
        payable(owner()).transfer(address(this).balance);
    }
}