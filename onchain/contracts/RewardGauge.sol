// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";
import "@openzeppelin/contracts/utils/cryptography/MessageHashUtils.sol";
import "./RewardToken.sol";

contract RewardGauge {
    using MessageHashUtils for bytes32;      // ← attaches .toEthSignedMessageHash()

    RewardToken public immutable token;
    mapping(address => uint16) public lastScore;   // 0–10 000 (basis-points)

    uint16  public constant THRESHOLD = 6000;      // ≥ 0.60 gets bonus
    uint256 public constant BONUS     = 1e18;      // 1 xREP

    constructor(address tokenAddr) { token = RewardToken(tokenAddr); }

    /// repHash = keccak256(abi.encodePacked(provider, scoreBps, epoch))
    function submitScore(
        bytes32 repHash,
        uint16  scoreBps,
        bytes   calldata sig
    ) external {
        // MessageHashUtils gives us the “Ethereum signed message” prefix
        bytes32 digest   = repHash.toEthSignedMessageHash();
        address provider = ECDSA.recover(digest, sig);

        require(scoreBps >= lastScore[provider], "score not improved");
        lastScore[provider] = scoreBps;

        if (scoreBps >= THRESHOLD) {
            token.mint(provider, BONUS);
        }
    }
}
