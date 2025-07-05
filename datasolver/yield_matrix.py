"""
YieldMatrix – minimal stub so Integration test passes.
Replace the body later with real DeFi adapters.
"""

from typing import List, Dict

def build_dataset(rfd: Dict) -> List[Dict]:
    # Offline hard-coded example rows
    combos = [(c, a) for c in rfd["chains"] for a in rfd["assets"]]
    rows: List[Dict] = []
    for chain, asset in combos:
        rows.append(
            {
                "chain": chain,
                "protocol": "MockProtocol",
                "asset": asset,
                "apy": "3.21",
                "tvl": "123.4M",
                "risk": "low",
            }
        )
    return rows
