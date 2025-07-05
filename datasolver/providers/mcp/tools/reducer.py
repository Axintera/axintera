# datasolver/providers/mcp/tools/reducer.py

"""ReduceAvgTool – averages numeric columns over a list of records."""
from typing import Dict, Any, List
from .tool import MCPTool

class ReduceAvgTool(MCPTool):
    # -------- metadata -------- #
    name: str = "reduce_avg"
    description: str = "Averages (mean) every numeric field in `records`."

    @property
    def capabilities(self) -> Dict[str, Any]:
        return {
            "aggregation": "mean",
            "input":  "List[Dict[str, number]]",
            "output": "List[Dict[str, number]] (single element)"
        }

    # -------- validation -------- #
    def validate_rfd(self, rfd: Dict[str, Any]) -> bool:
        # This tool is valid if the service name matches and 'records' is a list.
        return (
            rfd.get("service") == self.name
            and isinstance(rfd.get("records"), list)
        )

    # -------- core generator -------- #
    def generate_data(self, rfd: Dict[str, Any]) -> List[Dict[str, float]]:
        records: List[Dict[str, Any]] = rfd["records"]
        if not records:
            return [{}]

        keys = set().union(*records)
        out: Dict[str, float] = {}

        for k in keys:
            # Filter for numbers and ignore other types gracefully
            nums = [row[k] for row in records if isinstance(row.get(k), (int, float))]
            if nums:
                out[k] = sum(nums) / len(nums)

        return [out]

    # The router calls .generate(), so this method must exist.
    def generate(self, rfd: Dict[str, Any], **_) -> List[Dict[str, float]]:
        return self.generate_data(rfd)

    # *** FIX: Add the missing cost method ***
    def cost(self, rfd: Dict[str, Any]) -> float:
        """
        Calculate the cost of running this tool.
        For an averaging tool, a simple cost could be based on the number of records.
        Let's say it's 1 unit of cost per 100 records.
        """
        num_records = len(rfd.get("records", []))
        # Return a base cost of 1.0 plus cost per record
        # This ensures it's never zero and scales with input size.
        return 1.0 + (num_records / 100.0)