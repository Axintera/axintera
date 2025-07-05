import os, json
from .base import DeFiAdapter

MOCK_DB = json.loads("""[
  {"protocol":"Aave v3","asset":"ETH","apy":"3.42","tvl":"5.1B","audits":1,"oracle":"chainlink"}
]""")

class AaveAdapter(DeFiAdapter):
    chain = "eth"
    def top_yields(self, asset, depth):
        return [row for row in MOCK_DB if row["asset"] == asset][:5]
