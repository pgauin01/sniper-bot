// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

interface IUniswapV2Pair {
    function swap(uint amount0Out, uint amount1Out, address to, bytes calldata data) external;
    function token0() external view returns (address);
    function getReserves() external view returns (uint112 reserve0, uint112 reserve1, uint32 blockTimestampLast);
}

interface IUniswapV2Router {
    function swapExactTokensForTokens(
        uint amountIn,
        uint amountOutMin,
        address[] calldata path,
        address to,
        uint deadline
    ) external returns (uint[] memory amounts);
}

contract ArbSniper is Ownable {
    address constant UNISWAP_ROUTER = 0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D;
    
    address constant WETH = 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2;
    address constant USDC = 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48;

    constructor() Ownable(msg.sender) {}

    // 1. TRIGGER: Start Flash Swap on SUSHI
    function startFlashArbitrage(address pairAddress, uint amountWethToBorrow) external onlyOwner {
        bytes memory data = abi.encode(pairAddress);
        
        address token0 = IUniswapV2Pair(pairAddress).token0();
        uint amount0Out = token0 == WETH ? amountWethToBorrow : 0;
        uint amount1Out = token0 == WETH ? 0 : amountWethToBorrow;

        // Borrow WETH from Sushi
        IUniswapV2Pair(pairAddress).swap(amount0Out, amount1Out, address(this), data);
    }

    // 2. CALLBACK: Execute Trade
    function uniswapV2Call(address sender, uint amount0, uint amount1, bytes calldata data) external {
        uint wethBorrowed = amount0 == 0 ? amount1 : amount0;
        require(wethBorrowed > 0, "No WETH borrowed");

        // A. SELL HIGH on UNISWAP
        IERC20(WETH).approve(UNISWAP_ROUTER, wethBorrowed);
        
        address[] memory path = new address[](2);
        path[0] = WETH;
        path[1] = USDC;

        // Swap WETH -> USDC
        uint[] memory amounts = IUniswapV2Router(UNISWAP_ROUTER).swapExactTokensForTokens(
            wethBorrowed,
            0,
            path,
            address(this),
            block.timestamp + 60
        );
        uint usdcReceived = amounts[1];

        // B. CALCULATE REPAYMENT (INTERNAL MATH)
        // We do the math ourselves to avoid 'Empty Revert' from Router calls
        address pair = msg.sender;
        (uint112 reserve0, uint112 reserve1,) = IUniswapV2Pair(pair).getReserves();
        address token0 = IUniswapV2Pair(pair).token0();
        
        // We borrowed WETH (Out). We need to pay USDC (In).
        // If token0 is USDC, reserveIn is reserve0.
        (uint reserveIn, uint reserveOut) = token0 == USDC ? (uint(reserve0), uint(reserve1)) : (uint(reserve1), uint(reserve0));

        // Formula: AmountIn = (AmountOut * ReserveIn * 1000) / ((ReserveOut - AmountOut) * 997) + 1
        uint numerator = wethBorrowed * reserveIn * 1000;
        uint denominator = (reserveOut - wethBorrowed) * 997;
        uint amountToRepay = (numerator / denominator) + 1;

        require(usdcReceived > amountToRepay, "Not enough profit to repay loan!");

        // C. REPAY LOAN
        IERC20(USDC).transfer(pair, amountToRepay);

        // D. KEEP PROFIT
        // Remaining USDC stays in this contract
    }

    // Withdraw Functions
    function withdrawUSDC() external onlyOwner {
        uint balance = IERC20(USDC).balanceOf(address(this));
        IERC20(USDC).transfer(owner(), balance);
    }
}