# solverNode.py
"""
Main orchestration script for the Reppo solver node + Axintera reputation layer
───────────────────────────────────────────────────────────────────────────────
Modes
 • MOCK  – local run, fake wallet, no chain/IPFS
 • TEST  – real data generation, skips on-chain calls
 • PROD  – full pipeline (NFT check, IPFS, submitSolution)

Reputation layer
 • Creates   state/stats.db            (see reputation.py)
 • Records   served / success counters per wallet address
"""

import os, json, time, logging
from typing import Dict, Optional, List, Type
from dotenv import load_dotenv

# ─── Reppo skeleton imports ────────────────────────────────────────────
from rfdListener import RFDListener
from datasolver   import DataSolver
from ipfsUploader import upload_to_ipfs
from nftAuthorizer import NFTAuthorizer
from submitSolution import SolutionSubmitter

# ─── Axintera reputation helper (single-file) ─────────────────────────
# solverNode.py  – top of file, just after the other imports
import threading, asyncio, uvicorn, reputation
import score_service                   # <- the FastAPI app you created

# kick off background tasks once at start-up
reputation.init_db()
threading.Thread(target=lambda: asyncio.run(reputation.hourly_recalc()),
                 daemon=True).start()
threading.Thread(target=lambda: uvicorn.run("score_service:app",
                                            host="0.0.0.0", port=8000,
                                            log_level="warning"),
                 daemon=True).start()

# ─── logging config ───────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
LOGGER = logging.getLogger("SolverNode")

# ──────────────────────────────────────────────────────────────────────
class SolverNode:
    def __init__(
        self,
        test_mode: bool = False,
        mock_mode: bool = False,
        mcp_tools: Optional[List[Type]] = None,
    ):
        """
        Args:
            test_mode: process a local sample RFD, no chain calls
            mock_mode: generate mock data + mock tx hash (dev only)
            mcp_tools: optional list of MCP tool classes to inject
        """
        self.test_mode  = test_mode
        self.mock_mode  = mock_mode
        self.mcp_tools  = mcp_tools

        load_dotenv()

        # wallet address
        self.wallet_address = (
            "0xMockWalletAddress" if self.mock_mode else os.getenv("WALLET_ADDRESS")
        )
        if not self.wallet_address:
            raise ValueError("WALLET_ADDRESS must be set in .env")

        # core solver
        self.solver = DataSolver.from_env(mock_mode=self.mock_mode)

        # supporting components (skip in mock / test)
        if self.mock_mode or self.test_mode:
            self.authorizer = None
            self.submitter  = None
            self.listener   = None
        else:
            self.authorizer = NFTAuthorizer()
            self.submitter  = SolutionSubmitter()
            self.listener   = RFDListener()

        self._print_mode_banner()

    # ──────────────────────────────────────────────────────────────
    def _print_mode_banner(self):
        if self.mock_mode:
            mode = "MOCK"
            details = [
                "mock data generation",
                "mock blockchain responses",
                "no external services",
            ]
        elif self.test_mode:
            mode = "TEST"
            details = [
                "sample_rfd.json → dataset",
                "real data generation (if available)",
                "no blockchain interactions",
            ]
        else:
            mode = "PRODUCTION"
            details = [
                "real data generation",
                "full blockchain interactions",
                "requires Reppo NFT ownership",
            ]

        print(
            f"\nRunning in {mode} mode:\n"
            + "\n".join(f"- {d}" for d in details)
            + f"\n- wallet: {self.wallet_address}\n"
        )

    # ──────────────────────────────────────────────────────────────
    def process_rfd(self, rfd: Dict) -> Optional[Dict]:
        """Generate + store dataset, submit solution, update reputation."""
        rfd_id = rfd.get("rfd_id", "unknown")
        LOGGER.info("Processing RFD #%s", rfd_id)

        # NFT gate (prod only)
        if self.authorizer and not self.authorizer.has_nft(self.wallet_address):
            LOGGER.warning("Wallet %s lacks Reppo NFT – skipping", self.wallet_address)
            reputation.update_stats(self.wallet_address.lower(), ok=False)
            return None

        try:
            # 1. create dataset
            dataset_path = self.solver.solve(rfd)
            if not dataset_path:
                raise RuntimeError("datasolver returned empty path")

            # 2. mock path
            if self.mock_mode:
                cid = f"mockCID_{rfd_id}_{int(time.time())}"
                tx  = f"0x{'0'*40}_{rfd_id}_{int(time.time())}"
                result = {
                    "rfd_id": rfd_id,
                    "wallet": self.wallet_address,
                    "dataset_path": dataset_path,
                    "storage_uri": f"ipfs://{cid}",
                    "tx_hash": tx,
                }

            # 3. prod / test path
            else:
                storage_uri = upload_to_ipfs(dataset_path)
                if not storage_uri:
                    raise RuntimeError("IPFS upload failed")

                if self.submitter:
                    tx_hash = self.submitter.submit_solution(rfd_id, storage_uri)
                    if not tx_hash:
                        raise RuntimeError("submitSolution returned None")
                else:  # test_mode
                    tx_hash = "0xTESTMODE_TX"

                result = {
                    "rfd_id": rfd_id,
                    "wallet": self.wallet_address,
                    "dataset_path": dataset_path,
                    "storage_uri": storage_uri,
                    "tx_hash": tx_hash,
                }

            LOGGER.info("✅ RFD #%s processed", rfd_id)
            reputation.update_stats(self.wallet_address.lower(), ok=True)
            return result

        except Exception as exc:  # noqa: BLE001
            LOGGER.error("❌ RFD #%s failed: %s", rfd_id, exc)
            reputation.update_stats(self.wallet_address.lower(), ok=False)
            return None

    # ──────────────────────────────────────────────────────────────
    def run(self):
        if self.mock_mode or self.test_mode:
            self._run_local_mode()
        else:
            self._run_production()

    # local = mock or test
    def _run_local_mode(self):
        print("\nProcessing sample RFD...")
        try:
            with open("sample_rfd.json", "r", encoding="utf-8") as f:
                sample = json.load(f)
        except FileNotFoundError:
            print("sample_rfd.json not found – create one first.")
            return

        result = self.process_rfd(sample)
        if result:
            print(f"Sample RFD processed OK:\n{result}")
        else:
            print("Sample RFD failed – see logs.")

    # production
    def _run_production(self):
        if not self.listener:
            raise RuntimeError("Listener not initialised (should not happen)")

        print("Production mode – starting blockchain listener…")
        self.listener.listen_for_rfds(self.process_rfd)


# ─────────────── convenience CLI ─────────────────────────────
if __name__ == "__main__":
    import argparse, sys

    argp = argparse.ArgumentParser()
    argp.add_argument("--test", action="store_true", help="run sample_rfd.json")
    argp.add_argument("--mock", action="store_true", help="run with fake data/tx")
    args = argp.parse_args()

    node = SolverNode(test_mode=args.test, mock_mode=args.mock)
    node.run()
