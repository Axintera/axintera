#!/usr/bin/env python3
"""
Tiny FastAPI wrapper around SolverNode
* POST /execute_rfd – body = the RFD JSON
* registers itself with the mock router on startup
"""

import os, json, logging, httpx, asyncio
from fastapi import FastAPI, HTTPException
import uvicorn

from solverNode import SolverNode

log = logging.getLogger("solver-api")
logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)s  %(message)s")

node = SolverNode()
app  = FastAPI(title="Reppo Solver Node")

# --------------------------------------------------------------------------- #
@app.on_event("startup")
async def _register_with_router() -> None:
    router = os.getenv("MCP_SERVER_URL", "http://localhost:8000")
    my_url = os.getenv("SOLVER_URL",      "http://localhost:8001")
    payload = {"solver_url": my_url, "tools": ["yield_matrix"]}
    try:
        async with httpx.AsyncClient() as cli:
            await cli.post(f"{router}/register", json=payload, timeout=5)
        log.info("✔ Registered 'yield_matrix' with router %s", router)
    except Exception as exc:
        log.error("✖ Could not register with router – %s", exc)

# --------------------------------------------------------------------------- #
@app.post("/execute_rfd")
async def execute_rfd(rfd: dict):
    res = node.process_rfd(rfd)
    if not res:
        raise HTTPException(status_code=500, detail="Solver failed")
    return res

# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    port = int(os.getenv("SOLVER_PORT", "8001"))
    uvicorn.run(app, host="0.0.0.0", port=port)
