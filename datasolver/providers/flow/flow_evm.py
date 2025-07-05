import os
import json
from web3 import Web3
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class FlowEVMProvider:
    """
    Provider for interacting with the Flow EVM.
    Connects to a deployed contract to fetch real, gated yield rates.
    """
    def __init__(self):
        self.rpc_url = "https://mainnet.evm.nodes.onflow.org"
        self.web3 = Web3(Web3.HTTPProvider(self.rpc_url))
        
        # Get contract info from environment
        self.contract_address = os.getenv("FLOW_YIELD_GATE_CONTRACT")
        self.abi_path = "abis/FlowYieldGate_abi.json"
        
        if not self.contract_address:
            raise ValueError("FLOW_YIELD_GATE_CONTRACT not found in .env file.")
            
        self._initialize_contract()

    def _initialize_contract(self):
        """Loads the ABI and creates a contract instance."""
        try:
            with open(self.abi_path, 'r') as f:
                abi = json.load(f)
            
            self.contract = self.web3.eth.contract(
                address=self.web3.to_checksum_address(self.contract_address),
                abi=abi
            )
        except FileNotFoundError:
            raise FileNotFoundError(f"ABI file not found at {self.abi_path}. Please create it.")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize contract: {e}")

    async def check_nft_holdings(self, user_address: str, nft_collections: List[str]) -> int:
        """
        MOCK IMPLEMENTATION: Checks if a user holds a specific NFT.
        TODO: Integrate with a real NFT contract check using nftAuthorizer.py logic.
        """
        print(f"MOCK: Checking NFT holdings for {user_address}...")
        # For now, we simulate a score based on a non-zero address.
        return 150 if user_address.lower() != "0x0000000000000000000000000000000000000000" else 0

    async def calculate_reputation(self, user_address: str) -> int:
        """
        MOCK IMPLEMENTATION: Calculates a user's on-chain reputation.
        TODO: Implement real reputation logic (e.g., query transaction history, DeFi activity).
        """
        print(f"MOCK: Calculating reputation for {user_address}...")
        # Simulate a high reputation for demonstration purposes
        return 1250

    async def get_gated_yields(self, user_address: str, nft_score: int, reputation: int) -> List[Dict[str, Any]]:
        """
        REAL IMPLEMENTATION: Fetches yield rates from the deployed FlowYieldGate contract.
        """
        print(f"LIVE: Fetching yield rate for {user_address} from contract {self.contract_address}")
        
        try:
            # Call the 'getYieldRate' view function on the smart contract
            # Note: The contract owner must first call setPremiumAccess(user, true) for the user 
            # to get the premium rate. Otherwise, everyone gets the base rate.
            yield_rate_bps = self.contract.functions.getYieldRate(
                self.web3.to_checksum_address(user_address)
            ).call()
            
            apy = yield_rate_bps / 100.0  # Convert basis points to percentage

            return [
                {"protocol": "FlowYieldGate", "asset": "MIXED", "apy": apy, "tier": "live_from_contract"}
            ]

        except Exception as e:
            print(f"ERROR: Could not fetch from contract: {e}")
            return [
                {"protocol": "FlowYieldGate", "asset": "MIXED", "apy": 0.0, "tier": "error"}
            ]
