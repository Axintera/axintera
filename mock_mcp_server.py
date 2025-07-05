# mock_mcp_server.py
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import List, Dict, Any
import httpx
import logging
import uvicorn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MockMCPServer")

app = FastAPI(title="Mock MCP Server")

SOLVER_REGISTRY: Dict[str, str] = {}

class SolverInfo(BaseModel):
    solver_url: str
    tools: List[str]

@app.get("/")
def read_root():
    return {"message": "Mock MCP Server is running", "registry": SOLVER_REGISTRY}

@app.post("/register")
async def register_solver(info: SolverInfo):
    for tool in info.tools:
        SOLVER_REGISTRY[tool] = str(info.solver_url)
        logger.info(f"Registered tool '{tool}' for solver at {info.solver_url}")
    return {"status": "success", "message": f"Registered {len(info.tools)} tools."}

@app.post("/fulfill")
async def fulfill_rfd(rfd: Dict[str, Any]):
    service_needed = rfd.get("service")
    if not service_needed:
        raise HTTPException(status_code=400, detail="RFD must include a 'service' key.")

    logger.info(f"Received RFD for service: '{service_needed}'")

    if service_needed not in SOLVER_REGISTRY:
        logger.error(f"No solver found for service: '{service_needed}'")
        raise HTTPException(status_code=404, detail=f"No solver registered for service '{service_needed}'")

    solver_url = SOLVER_REGISTRY[service_needed]
    # The solver node expects to receive the RFD at its /execute_rfd endpoint
    forward_url = f"{solver_url}/execute_rfd" 
    
    logger.info(f"Forwarding RFD to solver at: {forward_url}")

    async with httpx.AsyncClient() as client:
        try:
            # POST the original RFD to the discovered solver
            response = await client.post(forward_url, json=rfd, timeout=15.0)
            response.raise_for_status() # Check for 4xx/5xx errors from the solver
            
            # *** FIX: Forward the solver's successful response back to the original caller ***
            return response.json()

        except httpx.RequestError as e:
            logger.error(f"Failed to forward RFD to solver: {e}")
            raise HTTPException(status_code=502, detail=f"Could not connect to solver at {solver_url}")
        except httpx.HTTPStatusError as e:
            # If the solver returns an error, forward that error information
            logger.error(f"Solver returned an error: {e.response.status_code} - {e.response.text}")
            # Try to return the solver's JSON error detail if it exists
            try:
                detail = e.response.json()
            except:
                detail = e.response.text
            raise HTTPException(status_code=e.response.status_code, detail=detail)


# *** FIX: Add this block to make the server runnable on a specific port ***
if __name__ == "__main__":
    """
    This allows you to run the mock server directly from the command line.
    `python mock_mcp_server.py`
    """
    logger.info("Starting Mock MCP Server...")
    # We explicitly set the port to 8000 to match our .env and test_client.py configuration
    uvicorn.run(app, host="0.0.0.0", port=8000)