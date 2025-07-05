#!/usr/bin/env python3
# solver_server.py

import os, json, logging, httpx
from typing import Dict, Any
from fastapi import FastAPI, HTTPException
from datasolver.providers.mcp.tools.reducer import ReduceAvgTool
from datasolver.providers.mcp.tools.yield_matrix_tool import YieldMatrixTool

# ── logging ─────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("solver-api")

# ── config ──────────────────────────────────────────────────────
MCP_SERVER = os.getenv("MCP_SERVER_URL", "http://localhost:8000")
SOLVER_URL = os.getenv("SOLVER_URL",     "http://localhost:8001")
AVAILABLE_TOOLS = [ReduceAvgTool, YieldMatrixTool]

app = FastAPI(title="Reppo Solver Node")

# ── register on startup ─────────────────────────────────────────
@app.on_event("startup")
async def register_with_router():
    payload = {
        "solver_url": SOLVER_URL,
        "tools":      [t().name for t in AVAILABLE_TOOLS]
    }
    for attempt in range(3):
        try:
            async with httpx.AsyncClient() as cli:
                resp = await cli.post(f"{MCP_SERVER}/register", json=payload, timeout=5)
                resp.raise_for_status()
                logger.info(f"✔ Registered {payload['tools']} with {MCP_SERVER}")
                return
        except Exception as e:
            logger.warning(f"Router registration failed (#{attempt+1}): {e}")
    logger.error("✖ Could not register with MCP router after 3 attempts")

# ── core endpoint ───────────────────────────────────────────────
@app.post("/execute_rfd")
async def execute_rfd(rfd: Dict[str,Any]):
    for ToolCls in AVAILABLE_TOOLS:
        tool = ToolCls()
        if tool.validate_rfd(rfd):
            out = tool.generate(rfd)
            return {"tool": tool.name, **out}
    raise HTTPException(status_code=404, detail=f"No tool for service '{rfd.get('service')}'")

# ── launcher ───────────────────────────────────────────────────
if __name__=="__main__":
    import uvicorn
    port = int(os.getenv("SOLVER_PORT","8001"))
    uvicorn.run("solver_server:app", host="0.0.0.0", port=port, log_level="info")
