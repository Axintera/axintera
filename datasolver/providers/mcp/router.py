import logging
import time
from typing import Dict, Any, List, Optional
from .client import MCPClient
from .tools.tool import MCPTool

# Use a specific logger for the router
log = logging.getLogger("RFDRouter")
# To see these logs during pytest, run: poetry run pytest -o log_cli=true -o log_cli_level=INFO

class RFDRouter:
    def __init__(self, mcp: MCPClient):
        self.mcp = mcp

    def fulfil(self, rfd: Dict[str, Any]) -> Dict[str, Any]:
        rfd_id = rfd.get("rfd_id", rfd.get("service", "unknown"))
        log.info(f"--- Fulfilling RFD: {rfd_id} ---")
        
        start = time.time()
        
        # --- FIX: Only collect the 'records' from the dependency result, not the whole dictionary ---
        # The recursive call returns a full dictionary {'elapsed': ..., 'records': [...]}. We only want the records.
        dependency_records = [
            record 
            for dep_rfd in rfd.get("dependencies", []) 
            for record in self.fulfil(dep_rfd)["records"]
        ]
        log.info(f"[{rfd_id}] Collected {len(dependency_records)} records from dependencies.")

        tool = self._choose_tool(rfd)
        if not tool:
            log.error(f"[{rfd_id}] No tool found that can satisfy this RFD.")
            raise RuntimeError(f"No tool can satisfy RFD: {rfd_id}")
            
        log.info(f"[{rfd_id}] Chose tool: '{tool.name}' (Cost: {tool.cost(rfd)})")
        
        generated_records = tool.generate(rfd)
        log.info(f"[{rfd_id}] Tool '{tool.name}' generated {len(generated_records)} records.")

        # The parts to be merged are now just the lists of records
        all_parts = []
        if dependency_records:
            all_parts.append(dependency_records)
        if generated_records:
            all_parts.append(generated_records)
        
        log.info(f"[{rfd_id}] Passing {len(all_parts)} chunks to be merged.")
        
        merged_records = self._merge(all_parts, rfd.get("aggregation", "union"))

        return {
            "elapsed": round(time.time() - start, 3),
            "tool": tool.name,
            "records": merged_records,
        }

    def _choose_tool(self, rfd) -> Optional[MCPTool]:
        cands = [(t.cost(rfd), t) for t in self.mcp._tools.values() if t.validate_rfd(rfd)]
        return min(cands, key=lambda item: item[0], default=(None, None))[1] if cands else None

    def _merge(self, chunks: List[List[Any]], mode: str) -> List[Any]:
        log.info(f"Merging {len(chunks)} chunks with mode '{mode}'")
        if not chunks:
            return []
        if len(chunks) == 1:
            return chunks[0]
            
        # --- FIX: The merge logic now correctly operates on a list of lists ---
        if mode in ("union", "concat"):
            output = []
            for chunk in chunks:
                # Each 'chunk' is already a list of records
                output.extend(chunk)
            log.info(f"Merged result has {len(output)} records.")
            return output
            
        if mode == "intersection":
            if not chunks[0]:
                return []
            # Convert records to tuples to make them hashable for set operations
            base = set(tuple(item.items()) for item in chunks[0])
            for chunk in chunks[1:]:
                base &= set(tuple(item.items()) for item in chunk)
            # Convert back to list of dicts
            return [dict(item) for item in base]
            
        log.warning(f"Unknown merge mode '{mode}'. Returning chunks as-is.")
        return chunks