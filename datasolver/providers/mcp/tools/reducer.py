"""ReduceAvgTool – averages numeric columns over a list of records."""
from typing import Dict, Any, List
from .tool import MCPTool   # local import from your providers package

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
            nums = [row[k] for row in records if isinstance(row.get(k), (int, float))]
            if nums:
                out[k] = sum(nums) / len(nums)

        return [out]   # tests expect a list with exactly one dict

    # alias so tests can call .generate()
    def generate(self, rfd: Dict[str, Any], **_) -> List[Dict[str, float]]:  # type: ignore[override]
        return self.generate_data(rfd)
