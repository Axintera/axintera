#!/usr/bin/env python3
"""
NFTAuthorizer – verifies NFT ownership, but can run in mock mode
"""

from __future__ import annotations
import os, json
from typing import List, Optional

from dotenv import load_dotenv

# Only import Web3 if we really need it (not in mock mode)
load_dotenv()
try:
    from web3 import Web3
    from web3.exceptions import ContractLogicError, Web3Exception
except ImportError:
    Web3 = None           # type: ignore

class NFTAuthorizer:
    """
    Verifies that a wallet owns at least one token in a given NFT collection.
    Set mock_mode=True (or SOLVER_MOCK_MODE=1 in your .env) to short-circuit
    every check and always return True – useful for local demos & CI.
    """
    # --------------------------------------------------------------------- #
    def __init__(self, *, mock_mode: bool | None = None) -> None:
        self.mock_mode: bool = (
            mock_mode
            if mock_mode is not None
            else os.getenv("SOLVER_MOCK_MODE", "0") == "1"
        )
        if self.mock_mode:
            # Nothing else to do – all methods will just return dummy values
            return

        if Web3 is None:
            raise RuntimeError("web3.py is not installed but mock_mode=False")

        # ─ read env ───────────────────────────────────────────────────────
        rpc             = os.environ["WEB3_RPC_URL"]
        contract_addr   = os.environ["NFT_CONTRACT_ADDRESS"]
        abi_path        = os.getenv("NFT_CONTRACT_ABI_PATH", "./abis/nft_abi.json")
        self.chain_id   = int(os.getenv("CHAIN_ID", "1"))

        self.web3       = Web3(Web3.HTTPProvider(rpc, request_kwargs={"timeout": 30}))
        with open(abi_path, "r") as fh:
            abi = json.load(fh)

        self.contract   = self.web3.eth.contract(
            address=self.web3.to_checksum_address(contract_addr),
            abi=abi,
        )

    # ------------------------------------------------------------------ #
    def has_nft(self, wallet: str, block: int | None = None) -> bool:
        """Does *wallet* own at least one token?"""
        if self.mock_mode:
            return True

        if not self.web3.is_address(wallet):
            raise ValueError(f"Invalid address: {wallet}")

        try:
            bal = self.contract.functions.balanceOf(
                self.web3.to_checksum_address(wallet)
            ).call({"block_identifier": block} if block else {})
            return bal > 0
        except (ContractLogicError, Web3Exception):
            return False

    # ------------------------------------------------------------------ #
    def get_owned_token_ids(self, wallet: str, block: int | None = None) -> List[int]:
        """Return **all** token IDs owned – empty list if none / mock mode."""
        if self.mock_mode:
            return []

        ids: list[int] = []
        if not self.has_nft(wallet, block):
            return ids

        bal = self.contract.functions.balanceOf(
            self.web3.to_checksum_address(wallet)
        ).call({"block_identifier": block} if block else {})

        for i in range(bal):
            try:
                tid = self.contract.functions.tokenOfOwnerByIndex(
                    self.web3.to_checksum_address(wallet), i
                ).call({"block_identifier": block} if block else {})
                ids.append(int(tid))
            except ContractLogicError:
                break
        return ids
