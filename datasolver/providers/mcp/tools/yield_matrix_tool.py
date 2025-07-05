# datasolver/providers/mcp/tools/yield_matrix_tool.py
from typing import Dict, Any
from .tool import MCPTool
from datasolver.yield_matrix import build_dataset

class YieldMatrixTool(MCPTool):
    name        = "yield_matrix"
    description = "Aggregates on-chain yields and returns a risk-scored matrix."

    def capabilities(self) -> Dict[str, Any]:
        return {
            "service": self.name,
            "version": "0.1.0",
            "inputs":  ["chains", "assets", "depth"],
            "outputs": ["chain", "protocol", "asset", "apy", "tvl", "risk","rank"],
        }

    def validate_rfd(self, rfd: Dict[str, Any]) -> bool:
        return rfd.get("service")==self.name and {"chains","assets"}<=rfd.keys()

    def cost(self, rfd: Dict[str,Any]) -> float:
        return 1.0

    def generate_data(self, rfd: Dict[str,Any]) -> Dict[str,Any]:
        return {"rows": build_dataset(rfd)}

    def generate(self, rfd: Dict[str,Any]) -> Dict[str,Any]:
        if not self.validate_rfd(rfd):
            raise ValueError("Invalid RFD for yield_matrix")
        return self.generate_data(rfd)
