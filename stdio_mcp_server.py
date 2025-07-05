#!/usr/bin/env python3
"""
Standard MCP Server (JSON-RPC 2.0 over stdin/stdout) for Amazon Q

* FINAL HARDCODED VERSION - GUARANTEED TO LOAD *
This is the user's working file with the new tool logic added manually
and hardcoded to prevent any possible crash.
"""

import json, sys, logging, os, httpx
from typing import Dict, Any, List

# ─────────────────────────  logging  ──────────────────────────
logging.basicConfig(
    level=logging.INFO,
    stream=sys.stderr,
    format="%(asctime)s  %(levelname)s  %(message)s",
)
log = logging.getLogger("mcp-server")

# ─────────────────────────  config  ───────────────────────────
ROUTER = os.getenv("ROUTER_URL", "http://localhost:8000")  # mock_mcp_server

YIELD_INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "chains": {"type": "array", "items": {"type": "string"}},
        "assets": {"type": "array", "items": {"type": "string"}},
        "depth":  {"type": "string"},
    },
    "required": ["chains", "assets"],
}

# --- NEW: Schema for our new tool ---
FLOW_YIELD_GATE_SCHEMA = {
    "type": "object",
    "properties": {
        "user_address": {"type": "string", "description": "The user's wallet address (e.g., 0x...)."},
        "nft_collections": {
            "type": "array",
            "items": {"type": "string"},
            "description": "A list of NFT collection identifiers to check."
        }
    },
    "required": ["user_address", "nft_collections"]
}


# ─────────────────────────  server class  ─────────────────────
class MCPServer:
    def __init__(self) -> None:
        self.initialized = False

    # ---------- tool dispatch -------------------------------------------------
    def _local_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "generate_data",
                "description": "Generate synthetic data based on schema",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "schema": {"type": "object"},
                        "count":  {"type": "integer", "default": 10},
                    },
                    "required": ["schema"],
                },
            },
            {
                "name": "query_data",
                "description": "Query existing data",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "table": {"type": "string"},
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "yield_matrix",
                "description": "Aggregates on-chain yield opportunities",
                "inputSchema": YIELD_INPUT_SCHEMA,
            },
            # --- The new tool definition ---
            {
                "name": "flow_yield_gate",
                "description": "HARDCODED: Get Flow EVM gated yield opportunities.",
                "inputSchema": FLOW_YIELD_GATE_SCHEMA,
            },
        ]

    # ---------- JSON-RPC handlers --------------------------------------------
    def handle_request(self, req: Dict[str, Any]) -> Dict[str, Any] | None:
        mid  = req.get("id")
        meth = req.get("method")
        prm  = req.get("params", {})

        try:
            if meth == "initialize":
                self.initialized = True
                return {
                    "jsonrpc": "2.0",
                    "id": mid,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {}, "resources": {}, "prompts": {}},
                        "serverInfo": {"name": "reppo-yield-mcp", "version": "0.2.0"},
                    },
                }

            if meth == "initialized":
                return None  # notification

            if meth == "tools/list":
                return {
                    "jsonrpc": "2.0",
                    "id": mid,
                    "result": {"tools": self._local_tools()},
                }

            if meth == "tools/call":
                name = prm.get("name")
                args = prm.get("arguments", {})
                if name == "generate_data":
                    return self._gen_data(mid, args)
                if name == "query_data":
                    return self._query_data(mid, args)
                if name == "yield_matrix":
                    return self._call_yield_matrix(mid, args)
                # --- The new tool dispatch ---
                if name == "flow_yield_gate":
                    return self._call_flow_yield_gate(mid, args)

                return {
                    "jsonrpc": "2.0",
                    "id": mid,
                    "error": {"code": -32602, "message": f"Unknown tool {name}"},
                }

            if meth in ("resources/list", "prompts/list"):
                return {"jsonrpc": "2.0", "id": mid, "result": {meth.split('/')[0]: []}}

            # default – method not found
            return {
                "jsonrpc": "2.0",
                "id": mid,
                "error": {"code": -32601, "message": f"Method not found: {meth}"},
            }

        except Exception as exc:  # broad catch so we always send a response
            log.exception("Handler error")
            return {
                "jsonrpc": "2.0",
                "id": mid,
                "error": {"code": -32603, "message": str(exc)},
            }

    # ---------- tool implementations -----------------------------------------

    def _gen_data(self, mid: int, args: Dict[str, Any]) -> Dict[str, Any]:
        schema = args.get("schema", {})
        count  = args.get("count", 10)
        rows = [{"id": i, "dummy": True} for i in range(count)]
        return self._simple_text_result(mid, f"Generated {count} rows:\n{json.dumps(rows,indent=2)}")

    def _query_data(self, mid: int, args: Dict[str, Any]) -> Dict[str, Any]:
        q   = args.get("query", "")
        tbl = args.get("table", "default")
        mock = [{"id": 1, "name": "foo"}, {"id": 2, "name": "bar"}]
        return self._simple_text_result(mid, f"Mock query `{q}` on `{tbl}`:\n{json.dumps(mock,indent=2)}")

    def _call_yield_matrix(self, mid: int, args: Dict[str, Any]) -> Dict[str, Any]:
        # forward to Reppo router
        rfd = {"service": "yield_matrix", **args}
        url = f"{ROUTER}/fulfill"
        try:
            with httpx.Client(timeout=30) as cli:
                res = cli.post(url, json=rfd)
                res.raise_for_status()
                data = res.json()
        except Exception as exc:
            return {
                "jsonrpc": "2.0",
                "id": mid,
                "error": {"code": -32603, "message": f"Router error: {exc}"},
            }

        return self._simple_text_result(mid, json.dumps(data, indent=2))

    # --- The new, self-contained, hardcoded tool implementation ---
    def _call_flow_yield_gate(self, mid: int, args: Dict[str, Any]) -> Dict[str, Any]:
        try:
            log.info(f"Executing hardcoded 'flow_yield_gate' with args: {args}")
            user_address = args.get("user_address", "not_provided")
            is_premium_user = user_address.lower() == "0x123"

            if is_premium_user:
                response_data = {"status": "success_simulated", "user_address": user_address, "nft_score": 150, "reputation": 1250, "premium_access": True, "available_yields": [{"protocol": "FlowLend", "asset": "USDC", "apy": 4.5, "tier": "basic"}, {"protocol": "FlowLend", "asset": "USDC", "apy": 7.8, "tier": "premium_unlocked"}]}
            else:
                response_data = {"status": "success_simulated", "user_address": user_address, "nft_score": 0, "reputation": 300, "premium_access": False, "available_yields": [{"protocol": "FlowLend", "asset": "USDC", "apy": 4.5, "tier": "basic"}]}
            
            result_text = json.dumps(response_data, indent=2)
            return self._simple_text_result(mid, result_text)
            
        except Exception as e:
            log.error(f"FATAL ERROR in _call_flow_yield_gate: {e}", exc_info=True)
            return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32000, "message": str(e)}}


    # ---------- helpers ------------------------------------------------------
    def _simple_text_result(self, mid: int, txt: str) -> Dict[str, Any]:
        return {
            "jsonrpc": "2.0",
            "id": mid,
            "result": {"content": [{"type": "text", "text": txt}]},
        }

    # ---------- main loop ----------------------------------------------------
    def run(self) -> None:
        log.info("MCP server ready (stdio).")
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                req = json.loads(line)
            except json.JSONDecodeError:
                continue
            resp = self.handle_request(req)
            if resp is not None:
                print(json.dumps(resp), flush=True)


# ─────────────────────────── entrypoint ─────────────────────────
if __name__ == "__main__":
    MCPServer().run()