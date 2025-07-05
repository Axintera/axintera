#!/usr/bin/env python3
"""
start_solver.py
───────────────
• --mode api  (default)   → launches solver_server.py  (FastAPI)
• --mode mcp              → launches fixed_mcp_server (stdio)
• --mode test             → runs the integration pytest
"""

import argparse, logging, os, subprocess, sys, asyncio

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("solver-startup")

def run_api():
    os.environ.setdefault("MCP_SERVER_URL", "http://localhost:8000")
    os.environ.setdefault("SOLVER_PORT",     "8001")
    os.environ.setdefault("SOLVER_URL",      "http://localhost:8001")
    cmd = [sys.executable, "solver_server.py"]
    log.info("⏩  Launching API solver: %s", " ".join(cmd))
    subprocess.call(cmd)

def run_mcp(timeout: int):
    from fixed_mcp_server import MCPServer
    async def _run():
        await asyncio.wait_for(MCPServer().run(), timeout=timeout)
    asyncio.run(_run())

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["api", "mcp", "test"], default="api")
    ap.add_argument("--timeout", type=int, default=30)
    args = ap.parse_args()

    if args.mode == "mcp":
        run_mcp(args.timeout)
    elif args.mode == "test":
        subprocess.call(["pytest", "tests/test_integration_mcp.py", "-q"])
    else:
        run_api()

if __name__ == "__main__":
    main()
