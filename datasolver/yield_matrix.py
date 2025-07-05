# datasolver/yield_matrix.py

import requests
from typing import Dict, Any, List

def get(url: str) -> Any:
    """Simple GET helper with timeout and error check."""
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    return resp.json()

def build_dataset(rfd: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Fetches DeFiLlama yield pools, filters by chains/assets,
    computes APY, TVL (in millions), risk, then returns
    the top-N entries ranked by APY.
    """
    # map our short codes to DeFiLlama chain names
    CHAIN_MAP = {"eth": "Ethereum", "arb": "Arbitrum", "sol": "Solana"}

    # normalize the input
    requested_chains = { CHAIN_MAP.get(c.lower(), c) for c in rfd["chains"] }
    requested_assets = { a.upper() for a in rfd["assets"] }
    # extract depth (e.g. "top_5" → 5)
    try:
        depth = int(str(rfd.get("depth", "top_5")).split("_")[-1])
    except ValueError:
        depth = 5

    # pull all pools
    raw = get("https://yields.llama.fi/pools")["data"]

    table: List[Dict[str, Any]] = []
    for p in raw:
        sym        = p.get("symbol", "").upper()
        chain_name = p.get("chain", "")

        if sym in requested_assets and chain_name in requested_chains:
            apy  = p.get("apy", 0.0) * 100                # from decimal to %
            tvl  = p.get("tvlUsd", 0.0) / 1e6             # TVL in millions
            table.append({
                "protocol": p.get("project", ""),
                "chain":    chain_name.lower(),           # back to lowercase
                "asset":    sym,
                "apy":      round(apy, 2),
                "tvl":      round(tvl, 2),
                "risk":     ("high"   if apy > 20
                             else "medium" if apy > 8
                             else "low"),
            })

    # sort by APY descending
    table.sort(key=lambda x: x["apy"], reverse=True)

    # take top‐N and assign rank
    result = []
    for idx, entry in enumerate(table[:depth], start=1):
        entry["rank"] = idx
        result.append(entry)

    return result
