// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

// --- 1. OPENZEPPELIN DEPENDENCIES (PASTED DIRECTLY) ---

interface IERC20 {
    function totalSupply() external view returns (uint256);
    function balanceOf(address account) external view returns (uint256);
    function transfer(address recipient, uint256 amount) external returns (bool);
    function allowance(address owner, address spender) external view returns (uint256);
    function approve(address spender, uint256 amount) external returns (bool);
    function transferFrom(address sender, address recipient, uint256 amount) external returns (bool);
}

abstract contract Context {
    function _msgSender() internal view virtual returns (address) {
        return msg.sender;
    }
}

abstract contract Ownable is Context {
    address private _owner;
    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);

    constructor(address initialOwner) {
        _transferOwnership(initialOwner);
    }

    function owner() public view virtual returns (address) {
        return _owner;
    }

    modifier onlyOwner() {
        require(owner() == _msgSender(), "Ownable: caller is not the owner");
        _;
    }

    function _transferOwnership(address newOwner) internal virtual {
        address oldOwner = _owner;
        _owner = newOwner;
        emit OwnershipTransferred(oldOwner, newOwner);
    }
}

// --- 2. YOUR DEBUG CONTRACT ---

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

contract ArbDebug is Ownable {
    // EVENTS (Flight Recorder)
    event Log(string message, uint256 val);
    event LogAddr(string message, address addr);

    address constant UNISWAP_ROUTER = 0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D;
    address constant WETH = 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2;
    address constant USDC = 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48;

    constructor() Ownable(msg.sender) {}

    function startFlashArbitrage(address pairAddress, uint amountWethToBorrow) external onlyOwner {
        emit LogAddr("1. Starting on Pair", pairAddress);
        
        bytes memory data = abi.encode(pairAddress);
        address token0 = IUniswapV2Pair(pairAddress).token0();
        emit LogAddr("2. Token0 found", token0);

        uint amount0Out = token0 == WETH ? amountWethToBorrow : 0;
        uint amount1Out = token0 == WETH ? 0 : amountWethToBorrow;

        emit Log("3. Triggering Swap", amountWethToBorrow);
        IUniswapV2Pair(pairAddress).swap(amount0Out, amount1Out, address(this), data);
    }

    function uniswapV2Call(address sender, uint amount0, uint amount1, bytes calldata data) external {
        emit Log("4. Inside Callback", amount0 + amount1);

        uint wethBorrowed = amount0 == 0 ? amount1 : amount0;
        
        // Step 5: Check Balance
        uint myWeth = IERC20(WETH).balanceOf(address(this));
        emit Log("5. WETH Balance", myWeth);

        // Step 6: Approve
        IERC20(WETH).approve(UNISWAP_ROUTER, wethBorrowed);
        emit Log("6. Approved Router", wethBorrowed);

        address[] memory path = new address[](2);
        path[0] = WETH;
        path[1] = USDC;

        // Step 7: Executing Swap
        emit Log("7. Swapping on Uniswap...", wethBorrowed);
        
        // --- THE DANGER ZONE ---
        uint[] memory amounts = IUniswapV2Router(UNISWAP_ROUTER).swapExactTokensForTokens(
            wethBorrowed,
            0,
            path,
            address(this),
            block.timestamp + 60
        );
        // -----------------------

        uint usdcReceived = amounts[1];
        emit Log("8. Swap Success. USDC Rx", usdcReceived);

        // Calculate Repayment
        address pair = msg.sender;
        (uint112 reserve0, uint112 reserve1,) = IUniswapV2Pair(pair).getReserves();
        address token0 = IUniswapV2Pair(pair).token0();
        (uint reserveIn, uint reserveOut) = token0 == USDC ? (uint(reserve0), uint(reserve1)) : (uint(reserve1), uint(reserve0));

        uint numerator = wethBorrowed * reserveIn * 1000;
        uint denominator = (reserveOut - wethBorrowed) * 997;
        uint amountToRepay = (numerator / denominator) + 1;

        emit Log("9. Calculated Repayment", amountToRepay);

        require(usdcReceived > amountToRepay, "Not enough profit to repay loan!");

        IERC20(USDC).transfer(pair, amountToRepay);
        emit Log("10. Loan Repaid!", amountToRepay);
    }
}