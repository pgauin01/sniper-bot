// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

// --- 1. INTERFACES (Flattened to avoid import errors) ---

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
    modifier onlyOwner() { require(owner() == _msgSender(), "Only Owner"); _; }
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

// --- 2. THE ARBITRAGE BOT ---

contract ArbSniper is Ownable {
    // Hardcoded Mainnet Addresses
    address constant UNISWAP_ROUTER = 0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D;
    address constant WETH = 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2;
    address constant USDC = 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48;

    constructor() Ownable(msg.sender) {}

    // A. TRIGGER: Borrow from the Cheap Exchange (SushiSwap)
    function startFlashArbitrage(address pairAddress, uint amountWethToBorrow) external onlyOwner {
        bytes memory data = abi.encode(pairAddress);
        address token0 = IUniswapV2Pair(pairAddress).token0();
        
        // We want to borrow WETH.
        // If token0 is WETH, we ask for amount0. If token1 is WETH, we ask for amount1.
        uint amount0Out = token0 == WETH ? amountWethToBorrow : 0;
        uint amount1Out = token0 == WETH ? 0 : amountWethToBorrow;

        // Initiate the Flash Swap
        IUniswapV2Pair(pairAddress).swap(amount0Out, amount1Out, address(this), data);
    }

    // B. CALLBACK: The logic that runs inside the loan
    function uniswapV2Call(address sender, uint amount0, uint amount1, bytes calldata data) external {
        uint wethBorrowed = amount0 == 0 ? amount1 : amount0;
        require(wethBorrowed > 0, "No WETH borrowed");

        // 1. SELL HIGH: Dump WETH on Uniswap
        IERC20(WETH).approve(UNISWAP_ROUTER, wethBorrowed);
        
        address[] memory path = new address[](2);
        path[0] = WETH;
        path[1] = USDC;

        uint[] memory amounts = IUniswapV2Router(UNISWAP_ROUTER).swapExactTokensForTokens(
            wethBorrowed, 
            0, 
            path, 
            address(this), 
            block.timestamp + 60
        );
        uint usdcReceived = amounts[1];

        // 2. INTERNAL MATH: Calculate Repayment
        // We calculate exactly how much USDC we owe SushiSwap manually to avoid errors.
        address pair = msg.sender;
        (uint112 reserve0, uint112 reserve1,) = IUniswapV2Pair(pair).getReserves();
        address token0 = IUniswapV2Pair(pair).token0();
        
        // Match reserves to tokens
        (uint reserveIn, uint reserveOut) = token0 == USDC ? (uint(reserve0), uint(reserve1)) : (uint(reserve1), uint(reserve0));

        // Uniswap V2 Formula: AmountIn = (AmountOut * ReserveIn * 1000) / ((ReserveOut - AmountOut) * 997) + 1
        uint numerator = wethBorrowed * reserveIn * 1000;
        uint denominator = (reserveOut - wethBorrowed) * 997;
        uint amountToRepay = (numerator / denominator) + 1;

        require(usdcReceived > amountToRepay, "Not enough profit to repay loan!");

        // 3. REPAY LOAN
        IERC20(USDC).transfer(pair, amountToRepay);
        
        // 4. PROFIT stays in this contract until you withdraw it
    }

    // C. WITHDRAW
    function withdrawUSDC() external onlyOwner {
        uint balance = IERC20(USDC).balanceOf(address(this));
        IERC20(USDC).transfer(owner(), balance);
    }
}