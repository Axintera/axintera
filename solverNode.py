# solverNode.py
"""
Main orchestration script for the Reppo solver node.

This script runs the solver as a persistent API server. On startup, it
registers itself with the Mock MCP Server (defined in the .env file).
It then listens for incoming RFD execution requests on the /execute_rfd endpoint.
"""
import os
import json
import time
import logging
from typing import Dict, Any, List, Type
from contextlib import asynccontextmanager

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
import uvicorn

# --- Project-specific Imports ---
from datasolver.providers.mcp.client import MCPClient
from datasolver.providers.mcp.router import RFDRouter
from datasolver.providers.mcp.tools.tool import MCPTool
from datasolver.providers.mcp.tools.reducer import ReduceAvgTool
import reputation

# --- Setup Logging and Environment ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
LOGGER = logging.getLogger("SolverNode")
load_dotenv()

# --- Solver Components ---
# Define what our solver can actually DO. Add all tool classes to this list.
AVAILABLE_TOOLS: List[Type[MCPTool]] = [
    ReduceAvgTool,
]

# The MCPClient in offline mode acts as a container for our tools.
mcp_client = MCPClient(tools=AVAILABLE_TOOLS)
# The RFDRouter uses the client to find the right tool for a job.
rfd_router = RFDRouter(mcp_client)


# *** FIX: Use the modern 'lifespan' manager for startup/shutdown events ***
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan manager for the solver node. Handles startup and shutdown events.
    """
    # --- Startup Logic ---
    mcp_server_url = os.getenv("MCP_SERVER_URL")
    solver_url = os.getenv("SOLVER_URL")

    if not mcp_server_url or not solver_url:
        LOGGER.warning("MCP_SERVER_URL or SOLVER_URL not found in .env. Skipping registration.")
        LOGGER.warning("Solver will run but will not be discovered by the MCP network.")
    else:
        tool_names = [tool_class().name for tool_class in AVAILABLE_TOOLS]
        registration_payload = {
            "solver_url": solver_url,
            "tools": tool_names
        }

        LOGGER.info(f"Attempting to register with MCP Server at {mcp_server_url}...")
        LOGGER.info(f"Registration payload: {json.dumps(registration_payload)}")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{mcp_server_url}/register", json=registration_payload, timeout=10)
                response.raise_for_status()
                LOGGER.info(f"Successfully registered with MCP Server: {response.json()}")
        except httpx.RequestError as e:
            LOGGER.error(f"Could not connect to MCP Server at {mcp_server_url}. Please ensure it's running. Error: {e}")
        except httpx.HTTPStatusError as e:
            LOGGER.error(f"Failed to register with MCP Server. Status: {e.response.status_code}, Body: {e.response.text}")
    
    # This 'yield' is where the application runs while it's alive.
    yield
    
    # --- Shutdown Logic (if any) ---
    LOGGER.info("Solver node is shutting down.")

# --- Initialize FastAPI App ---
# Pass the lifespan manager to the FastAPI app.
app = FastAPI(title="Reppo Solver Node", lifespan=lifespan)


# --- Core API Endpoints ---
@app.get("/")
def read_root():
    """Root endpoint for health checks."""
    tool_names = [tool().name for tool in AVAILABLE_TOOLS]
    return {
        "message": "Reppo Solver Node is running",
        "available_tools": tool_names
    }

@app.post("/execute_rfd")
async def execute_rfd(rfd: Dict[str, Any], request: Request):
    """
    This is the primary endpoint for the solver. The MCP Server will call this.
    It takes an RFD, uses the router to find the right tool, executes it,
    and returns the result.
    """
    provider_id = request.client.host # Using client IP as a simple provider ID
    service = rfd.get('service', 'unknown')
    LOGGER.info(f"Received RFD for service '{service}' from {provider_id}")

    start_time = time.time()
    ok = False
    try:
        # Use the router to fulfill the request
        result = rfd_router.fulfil(rfd)
        ok = True
        elapsed = time.time() - start_time
        LOGGER.info(f"Successfully fulfilled RFD for '{service}' in {elapsed:.2f}s")
        # Add elapsed time to the response
        result['elapsed_seconds'] = elapsed
        return result

    except Exception as e:
        LOGGER.error(f"Failed to fulfill RFD for '{service}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Update reputation stats regardless of success or failure
        reputation.update_stats(provider_id, ok)


# --- Main execution block ---
if __name__ == "__main__":
    """
    This allows you to run the solver directly from the command line.
    `python solverNode.py`
    """
    LOGGER.info("Starting Reppo Solver Node...")
    # Get port from .env, default to 8001
    port = int(os.getenv("SOLVER_PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)