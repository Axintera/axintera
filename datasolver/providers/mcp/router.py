"""
RFD Router – picks cheapest validating tool & merges sub-results.
"""
import logging, time
from typing import Dict, Any, List, Tuple, Optional
from .client import MCPClient
from .tools.tool import MCPTool

log = logging.getLogger("RFDRouter")

class RFDRouter:
    def __init__(self, mcp: MCPClient): self.mcp = mcp

    def fulfil(self, rfd: Dict[str, Any]) -> Dict[str, Any]:
        start   = time.time()
        parts   = [self.fulfil(d) for d in rfd.get("dependencies", [])]
        tool    = self._choose_tool(rfd)
        if not tool:
            raise RuntimeError("No tool can satisfy RFD")
        parts.append(tool.generate(rfd))
        return {
            "elapsed": round(time.time()-start, 3),
            "tool": tool.name,
            "records": self._merge(parts, rfd.get("aggregation","union")),
        }

    # ---------- helpers ----------
    def _choose_tool(self, rfd) -> Optional[MCPTool]:
        cands = [(t.cost(rfd), t) for t in self.mcp._tools.values()
                 if t.validate_rfd(rfd)]
        return min(cands, default=(None,None))[1] if cands else None

    def _merge(self, chunks: List[Any], mode: str):
        if len(chunks)==1: return chunks[0]
        if mode in ("union","concat"):
            out=[]; [out.extend(c) for c in chunks]; return out
        if mode=="intersection":
            base=set(map(tuple,chunks[0]))
            for c in chunks[1:]: base &= set(map(tuple,c))
            return [list(x) for x in base]
        return chunks
