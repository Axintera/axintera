// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title FlowYieldGate
 * @dev A contract to manage gated access to yield opportunities based on
 *      NFT holdings and on-chain reputation scores on Flow EVM.
 */
contract FlowYieldGate {
    // --- State Variables ---
    
    // Base yield rate for all users
    uint256 public baseRate = 500; // 5.00%
    
    // Bonus for users with premium access
    uint256 public premiumBonus = 250; // +2.50%

    // Mapping from user address to their reputation score
    mapping(address => uint256) public reputationScores;
    
    // Mapping to grant premium access (can be set by an owner/admin)
    mapping(address => bool) public premiumAccess;
    
    // Address of the contract owner, who can manage access
    address public owner;

    // --- Events ---
    event ReputationUpdated(address indexed user, uint256 newScore);
    event PremiumAccessGranted(address indexed user);
    event PremiumAccessRevoked(address indexed user);

    // --- Modifiers ---
    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can call this function");
        _;
    }
    
    // --- Constructor ---
    constructor() {
        owner = msg.sender;
    }

    // --- Core Logic ---
    
    /**
     * @dev Get the applicable yield rate for a given user.
     * @param user The address of the user.
     * @return The yield rate in basis points (e.g., 750 means 7.50%).
     */
    function getYieldRate(address user) public view returns (uint256) {
        if (premiumAccess[user]) {
            return baseRate + premiumBonus;
        }
        return baseRate;
    }
    
    // --- Admin Functions ---

    /**
     * @dev Update a user's reputation score. This could be called by an off-chain oracle.
     *      If the score exceeds a threshold, grant them premium access.
     * @param user The address of the user to update.
     * @param score The new reputation score.
     */
    function updateReputation(address user, uint256 score) external onlyOwner {
        reputationScores[user] = score;
        emit ReputationUpdated(user, score);
        
        // Automatically grant premium access if score is high
        if (score > 1000) {
            if (!premiumAccess[user]) {
                premiumAccess[user] = true;
                emit PremiumAccessGranted(user);
            }
        }
    }

    /**
     * @dev Manually grant or revoke premium access for a user.
     * @param user The address of the user.
     * @param hasAccess The new premium access status.
     */
    function setPremiumAccess(address user, bool hasAccess) external onlyOwner {
        premiumAccess[user] = hasAccess;
        if (hasAccess) {
            emit PremiumAccessGranted(user);
        } else {
            emit PremiumAccessRevoked(user);
        }
    }
}
