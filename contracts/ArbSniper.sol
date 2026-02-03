// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

interface IUniswapV2Router {
    function getAmountsOut(uint amountIn, address[] calldata path) external view returns (uint[] memory amounts);
    function swapExactTokensForTokens(
        uint amountIn,
        uint amountOutMin,
        address[] calldata path,
        address to,
        uint deadline
    ) external returns (uint[] memory amounts);
}

interface IUniswapV2Pair {
    function swap(uint amount0Out, uint amount1Out, address to, bytes calldata data) external;
}

contract ArbSniper is Ownable {
    address constant UNISWAP_ROUTER = 0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D;
    address constant SUSHISWAP_ROUTER = 0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F;
    
    address constant WETH = 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2;
    address constant USDC = 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48;

    constructor() Ownable(msg.sender) {}

    // 1. TRIGGER: Start the Flash Loan (Borrow WETH)
    function startFlashArbitrage(address tokenPair, uint amountToBorrow) external onlyOwner {
        bytes memory data = abi.encode(UNISWAP_ROUTER, SUSHISWAP_ROUTER);
        // Borrow WETH (Token 1 in WETH/USDC pair usually, but depends on sort order)
        // We assume we are calling the pair where WETH is token 1 for this simulation
        IUniswapV2Pair(tokenPair).swap(0, amountToBorrow, address(this), data);
    }

    // 2. CALLBACK: Execute the Trades
    function uniswapV2Call(address sender, uint amount0, uint amount1, bytes calldata data) external {
        uint amountBorrowed = amount1; 
        require(amountBorrowed > 0, "No WETH borrowed");

        // A. Sell WETH on Uniswap (Expensive) -> Get USDC
        IERC20(WETH).approve(UNISWAP_ROUTER, amountBorrowed);
        
        address[] memory pathSell = new address[](2);
        pathSell[0] = WETH;
        pathSell[1] = USDC;

        uint[] memory amounts1 = IUniswapV2Router(UNISWAP_ROUTER).swapExactTokensForTokens(
            amountBorrowed,
            0,
            pathSell,
            address(this),
            block.timestamp + 60
        );
        uint usdcReceived = amounts1[1];

        // B. Buy WETH on SushiSwap (Cheap) -> Get WETH
        IERC20(USDC).approve(SUSHISWAP_ROUTER, usdcReceived);

        address[] memory pathBuy = new address[](2);
        pathBuy[0] = USDC;
        pathBuy[1] = WETH;

        // We spend all USDC to buy as much WETH as possible
        uint[] memory amounts2 = IUniswapV2Router(SUSHISWAP_ROUTER).swapExactTokensForTokens(
            usdcReceived,
            0,
            pathBuy,
            address(this),
            block.timestamp + 60
        );
        uint wethBought = amounts2[1];

        // C. Repay Loan + 0.3% Fee
        uint fee = (amountBorrowed * 3) / 997 + 1;
        uint amountToRepay = amountBorrowed + fee;

        require(wethBought >= amountToRepay, "Not enough profit to repay loan!");

        // Pay back the pair
        IERC20(WETH).transfer(msg.sender, amountToRepay);

        // Remaining WETH is our profit!
    }

    // Withdraw Functions
    function withdrawETH() external onlyOwner {
        payable(owner()).transfer(address(this).balance);
    }

    function withdrawToken(address token) external onlyOwner {
        uint balance = IERC20(token).balanceOf(address(this));
        IERC20(token).transfer(owner(), balance);
    }
}