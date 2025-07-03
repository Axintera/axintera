// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;
import "@openzeppelin/contracts/token/ERC20/ERC20.sol";

contract RewardToken is ERC20 {
    constructor() ERC20("Axintera Reward", "xREP") {}
    function mint(address to, uint256 amt) external { _mint(to, amt); }
}
