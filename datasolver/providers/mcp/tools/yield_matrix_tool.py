# datasolver/providers/mcp/tools/yield_matrix_tool.py
from typing import Dict, Any, List
from .tool import MCPTool
from datasolver.yield_matrix import build_dataset

class YieldMatrixTool(MCPTool):
    name: str = "yield_matrix"
    description: str = (
        "Aggregates on-chain yields and returns a risk-scored matrix."
    )

    # ------------------------------------------------------------------
    # 1. minimal metadata for discovery
    # ------------------------------------------------------------------
    def capabilities(self) -> Dict[str, Any]:
        return {
            "service": self.name,
            "version": "0.1.0",
            "inputs":  ["chains", "assets", "depth", "window"],
            "outputs": ["chain", "protocol", "asset", "apy", "tvl", "risk"],
        }

    # ------------------------------------------------------------------
    # 2. sanity-check the RFD
    # ------------------------------------------------------------------
    def validate_rfd(self, rfd: Dict[str, Any]) -> bool:
        return rfd.get("service") == self.name and {"chains", "assets"} <= rfd.keys()

    # ------------------------------------------------------------------
    # 3. actual work
    # ------------------------------------------------------------------
    def generate_data(self, rfd: Dict[str, Any]) -> Dict[str, Any]:
        return {"rows": build_dataset(rfd)}

    # ------------------------------------------------------------------
    # 4. RFDRouter tie-breaker
    # ------------------------------------------------------------------
    def cost(self, rfd):           # type: ignore[override]
        return 1.0

    # ------------------------------------------------------------------
    # 5. **NEW** entrypoint RFDRouter expects
    # ------------------------------------------------------------------
    def generate(self, rfd: Dict[str, Any]):  # type: ignore[override]
        if not self.validate_rfd(rfd):
            raise ValueError("Invalid RFD for yield_matrix")
        return self.generate_data(rfd)
