#!/usr/bin/env python3
"""
solver_server.py
────────────────
FastAPI service that wraps the existing SolverNode class.

▪ POST /execute_rfd –> SolverNode.process_rfd(…)
▪ On startup registers tool 'yield_matrix' with the mock router
"""

import os, json, logging, httpx, uvicorn
from fastapi import FastAPI, HTTPException
from solverNode import SolverNode                     # ← your long class file

log  = logging.getLogger("solver-api")
node = SolverNode()                                   # production instance

app = FastAPI(title="Reppo Solver Node")

# ───────────────────────── REST entrypoint ──────────────────────────
@app.post("/execute_rfd")
async def execute_rfd(rfd: dict):
    """Router (or Q) sends Requests-for-Data here"""
    result = node._process_rfd(rfd)         # ← use the real method
    if result is None:
        raise HTTPException(500, "Solver failed")
    return result                                     # a plain dict

# ───────────────────── register with router on start ───────────────
ROUTER_URL  = os.getenv("MCP_SERVER_URL", "http://localhost:8000")
SOLVER_PORT = int(os.getenv("SOLVER_PORT", 8001))
SOLVER_URL  = os.getenv("SOLVER_URL", f"http://localhost:{SOLVER_PORT}")

@app.on_event("startup")
async def register_tool():
    payload = {"solver_url": SOLVER_URL, "tools": ["yield_matrix"]}
    try:
        async with httpx.AsyncClient() as cli:
            res = await cli.post(f"{ROUTER_URL}/register", json=payload, timeout=10)
            res.raise_for_status()
        log.info("✔ Registered 'yield_matrix' with router %s", ROUTER_URL)
    except Exception as exc:
        log.error("✖ Could not register with router – %s", exc)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=SOLVER_PORT)
