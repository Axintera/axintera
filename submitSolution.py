#!/usr/bin/env python
import os, json, logging
from typing import Optional

from dotenv import load_dotenv
from web3 import Web3
from ipfsUploader import upload_to_ipfs
import reputation                        # ← new helper

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("SolutionSubmitter")

PROVIDER_ID = os.getenv("WALLET_ADDRESS", "unknown_provider").lower()
reputation.init_db()

class SolutionSubmitter:
    GAS_LIMIT = 200_000

    def __init__(self) -> None:
        self.rpc       = os.getenv("WEB3_RPC_URL")
        self.addr      = os.getenv("EXCHANGE_CONTRACT_ADDRESS")
        self.abi_path  = os.getenv("EXCHANGE_CONTRACT_ABI_PATH", "./abis/exchange_abi.json")
        self.pk        = os.getenv("PRIVATE_KEY")
        self.chain_id  = int(os.getenv("CHAIN_ID", "1"))

        for k, v in {"WEB3_RPC_URL": self.rpc, "EXCHANGE_CONTRACT_ADDRESS": self.addr,
                     "PRIVATE_KEY": self.pk}.items():
            if not v:
                raise EnvironmentError(f"Missing env var {k}")

        self.w3 = Web3(Web3.HTTPProvider(self.rpc))
        if not self.w3.is_connected():
            raise ConnectionError("RPC not reachable")

        with open(self.abi_path, "r", encoding="utf-8") as f:
            abi = json.load(f)
        self.contract = self.w3.eth.contract(
            address=self.w3.to_checksum_address(self.addr),
            abi=abi,
        )
        self.acct = self.w3.eth.account.from_key(self.pk)

    # ------------------------------------------------------------
    def submit_solution(self, rfd_id: int, file_path: str) -> Optional[str]:
        try:
            cid_uri = upload_to_ipfs(file_path)
            if not cid_uri:
                raise RuntimeError("IPFS upload failed")

            nonce = self.w3.eth.get_transaction_count(self.acct.address)
            tx    = self.contract.functions.submitSolution(rfd_id, cid_uri).build_transaction(
                {"from": self.acct.address, "nonce": nonce, "gas": self.GAS_LIMIT,
                 "gasPrice": self.w3.eth.gas_price, "chainId": self.chain_id}
            )
            signed  = self.w3.eth.account.sign_transaction(tx, self.pk)
            tx_hash = self.w3.eth.send_raw_transaction(signed.rawTransaction)
            log.info("✅ submitSolution tx %s", self.w3.to_hex(tx_hash))

            reputation.update_stats(PROVIDER_ID, True)
            return self.w3.to_hex(tx_hash)

        except Exception as exc:                       # noqa: BLE001
            log.error("❌ submitSolution failed: %s", exc)
            reputation.update_stats(PROVIDER_ID, False)
            return None

    def is_connected(self) -> bool:
        return self.w3.is_connected() and self.w3.eth.chain_id == self.chain_id
