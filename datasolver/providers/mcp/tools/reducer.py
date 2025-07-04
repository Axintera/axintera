"""ReduceAvgTool – averages numeric columns in incoming record list."""
from typing import Dict, Any, List
from .tool import MCPTool
import statistics

class ReduceAvgTool(MCPTool):
    def __init__(self):
        super().__init__("reduce_avg", "Averages numeric fields")

    def validate_rfd(self, rfd: Dict[str, Any]) -> bool:
        return rfd.get("service") == "reduce_avg" and "records" in rfd

    def generate(self, rfd: Dict[str, Any], **kw) -> List[Dict[str, Any]]:
        rows = rfd["records"]
        nums = {k: [] for k,v in rows[0].items() if isinstance(v,(int,float))}
        for row in rows:
            for k,v in row.items():
                if k in nums and isinstance(v,(int,float)): nums[k].append(v)
        return [{k: statistics.mean(v) for k,v in nums.items()}]

    def cost(self, rfd): return 1
