#!/usr/bin/env python3
"""
SolverNode – core logic: read an RFD, generate a dataset, (optionally)
upload to IPFS & submit an on-chain solution.
"""

from __future__ import annotations
import os, json, logging
from typing import Dict, Any

from datasolver.datasolver import DataSolver
import ipfsUploader
from nftAuthorizer import NFTAuthorizer
import submitSolution

log = logging.getLogger("SolverNode")
logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)s  %(message)s")

# --------------------------------------------------------------------------- #
class SolverNode:
    def __init__(self) -> None:
        self.mock_mode = os.getenv("SOLVER_MOCK_MODE", "0") == "1"
        log.info("Initialising SolverNode   mock_mode=%s", self.mock_mode)

        # 1) dataset generator ------------------------------------------------
        self.data_solver = DataSolver()

        # 2) chain-related helpers -------------------------------------------
        self.nft     = NFTAuthorizer(mock_mode=self.mock_mode)
        self.submit  = submitSolution if not self.mock_mode else None
        self.ipfs_up = ipfsUploader    if not self.mock_mode else None

    # --------------------------------------------------------------------- #
    def process_rfd(self, rfd: Dict[str, Any]) -> Dict[str, Any] | bool:
        """Core business logic – returns structured result or False on failure."""
        rfd_id = rfd.get("rfd_id", "unknown")
        log.info("▶ processing RFD %s", rfd_id)

        # a) dataset ---------------------------------------------------------
        outfile = self.data_solver.solve(rfd)
        if not outfile:
            log.error("dataset generation failed")
            return False

        result: dict[str, Any] = {
            "rfd_id":        rfd_id,
            "dataset_path":  outfile,
            "mock_mode":     self.mock_mode,
        }

        # b) mock path ends here --------------------------------------------
        if self.mock_mode:
            log.info("✓ mock mode – skipping NFT/IPFS/on-chain steps")
            return result

        # c) check NFT -------------------------------------------------------
        wallet = os.environ.get("WALLET_ADDRESS", "")
        if not self.nft.has_nft(wallet):
            log.error("wallet %s does NOT own the required NFT – aborting", wallet)
            return False

        # d) IPFS upload -----------------------------------------------------
        cid_uri = self.ipfs_up.upload_to_ipfs(outfile)
        if not cid_uri:
            log.error("IPFS upload failed")
            return False
        result["storage_uri"] = cid_uri

        # e) submit on chain -------------------------------------------------
        tx_hash = self.submit.submit_solution(rfd_id, cid_uri)
        if not tx_hash:
            log.error("solution submission failed")
            return False
        result["tx_hash"] = tx_hash

        log.info("✓ RFD %s completed", rfd_id)
        return result
