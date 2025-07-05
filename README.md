
# Axintera Solver Node

![Version](https://img.shields.io/badge/Version-1.0.0-blue.svg) ![License](https://img.shields.io/badge/License-MIT-green.svg)

## Overview

The Axintera Solver Node is an autonomous agent designed to operate within the Reppo MCP (Multi-Capability Protocol) Network. Its primary function is to listen for and fulfill data requests, known as "intents," by leveraging a modular set of tools.

This implementation uses a `stdio_mcp_server.py` script as its core, which communicates with a client via JSON-RPC 2.0 over standard input/output. This allows for seamless integration with development environments and command-line interfaces like the `q` CLI.

The purpose of this project is to demonstrate how a solver node can be extended from a simple public data provider to an agent capable of enforcing business logic and providing differentiated, gated access to premium services based on a user's on-chain identity.

## Core Architecture

-   **`stdio_mcp_server.py`**: The main entry point and communication handler. It listens for JSON-RPC requests, discovers available tools, and dispatches requests to the appropriate implementation logic.
-   **Tool-Based Design**: Functionality is encapsulated in "tools." Each tool has a defined name, description, and input schema, making the system modular and extensible.
-   **Smart Contract Integration (Simulated)**: The system is designed to interact with on-chain smart contracts to validate user credentials or retrieve state-dependent data. For this demonstration, the contract interaction is hardcoded within the server to ensure stability and focus on the solver's internal logic.

## Setup and Installation

### Prerequisites

-   Python 3.11+
-   Poetry for dependency management

### Installation Steps

1.  **Clone the repository:**
    ```bash
    git clone <your-repository-url>
    cd solver-node
    ```

2.  **Configure Environment Variables:**
    This project requires certain environment variables. Create a `.env` file in the root directory. For this demo, only `ROUTER_URL` is used by the `yield_matrix` tool.
    ```bash
    # .env
    ROUTER_URL="http://localhost:8000"
    ```

3.  **Install Dependencies using Poetry:**
    Using Poetry is required to ensure all dependencies, such as `web3`, are installed correctly in a managed environment.

    ```bash
    # Configure Poetry to create the virtual environment inside the project folder
    poetry config virtualenvs.in-project true

    # Install all dependencies from the poetry.lock file
    poetry install
    ```

## Running the Solver

To interact with the solver, you must run the client from within the Poetry environment. This ensures that the Python interpreter and all required libraries are correctly loaded.

```bash
# This command starts the q CLI and connects it to the solver node
poetry run q
```

The server will load, and you can begin interacting with its tools.

## Available Tools

You can list all available tools by running `/tools` in the `q` CLI.

### 1. `yield_matrix` (Public Data Tool)

-   **Purpose**: This tool aggregates publicly available yield data from various DeFi protocols across multiple blockchain networks. It functions as a general-purpose, public data service.
-   **Usage**:
    ```bash
    /use yield_matrix for {"chains": ["eth"], "assets": ["USDC"]}
    ```
-   **Parameters**:
    -   `chains` (List[str]): A list of blockchain networks to query (e.g., `["eth", "arb"]`).
    -   `assets` (List[str]): A list of asset symbols to find yields for (e.g., `["USDC", "WETH"]`).
-   **Output**: Returns a JSON object containing a matrix of yield opportunities matching the query. This data is the same for all users.

### 2. `flow_yield_gate` (Gated Access Tool)

-   **Purpose**: This tool demonstrates a premium, gated service. It is designed to provide different data based on the user's identity. The logic simulates checking an on-chain credential (like an NFT holding) and returning a corresponding data payload. **For this demo, the logic is hardcoded.**
-   **Usage (Standard User)**:
    ```bash
    /use flow_yield_gate for {"user_address": "0x456abc", "nft_collections": ["any"]}
    ```
-   **Output (Standard User)**:
    ```json
    {
      "status": "success_simulated",
      "user_address": "0x456abc",
      "nft_score": 0,
      "reputation": 300,
      "premium_access": false,
      "available_yields": [
        {
          "protocol": "FlowLend",
          "asset": "USDC",
          "apy": 4.5,
          "tier": "basic"
        }
      ]
    }
    ```
-   **Usage (Premium User)**: The tool is hardcoded to recognize the address `0x123` as a premium user.
    ```bash
    /use flow_yield_gate for {"user_address": "0x123", "nft_collections": ["any"]}
    ```
-   **Output (Premium User)**:
    ```json
    {
      "status": "success_simulated",
      "user_address": "0x123",
      "nft_score": 150,
      "reputation": 1250,
      "premium_access": true,
      "available_yields": [
        {
          "protocol": "FlowLend",
          "asset": "USDC",
          "apy": 4.5,
          "tier": "basic"
        },
        {
          "protocol": "FlowLend",
          "asset": "USDC",
          "apy": 7.8,
          "tier": "premium_unlocked"
        }
      ]
    }
    ```

## Smart Contract: `FlowYieldGate.sol`

-   **Purpose**: The `flow_yield_gate` tool is designed to integrate with this smart contract. The contract's purpose is to act as an on-chain "gatekeeper" for premium services. By storing the business logic on-chain, we separate it from the solver node, making the system more decentralized and transparent.
-   **Key Functions**:
    -   `getYieldRate(address user)`: A public view function that returns a yield rate. It checks if the `user` has `premiumAccess` and returns either the `baseRate` or the `baseRate` + `premiumBonus`.
    -   `setPremiumAccess(address user, bool hasAccess)`: An owner-only function to manually grant or revoke premium status for a user.
    -   `updateReputation(address user, uint256 score)`: An owner-only function designed to be called by an off-chain oracle or trusted service. It updates a user's reputation score and can automatically grant premium access if a threshold is met.
-   **State Variables**:
    -   `baseRate`: The default yield rate for all users.
    -   `premiumBonus`: The additional yield points granted to premium users.
    -   `premiumAccess`: A mapping from a user's address to their premium status (`bool`).

## Project Goals

This project demonstrates the evolution of a solver node from a simple data aggregator to a state-aware agent capable of enforcing business logic. By implementing a tool with conditional, user-specific logic, we prove the viability of this architecture for building real-world decentralized applications that require:
-   Tiered access levels (e.g., Free vs. Premium).
-   Rewarding users based on on-chain activity or asset ownership.
-   Creating personalized data experiences in a trust-minimized way.

This serves as a foundational step for creating more complex, economically-aware autonomous agents on the web.
