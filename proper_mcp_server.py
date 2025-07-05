#!/usr/bin/env python3
"""
Proper MCP Server for Amazon Q
This implements the MCP protocol over stdio as expected by Q
"""

import asyncio
import json
import logging
import sys
from typing import Any, Dict, List, Optional, Sequence
import httpx

# Configure logging to stderr so it doesn't interfere with MCP communication
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger("MCPServer")

# Your solver registry
SOLVER_REGISTRY: Dict[str, str] = {
    "execute_rfd": "http://localhost:8001"
}

class MCPServer:
    def __init__(self):
        self.request_id = 0
    
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP requests"""
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")
        
        logger.info(f"Received request: {method}")
        
        try:
            if method == "initialize":
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {},
                            "logging": {}
                        },
                        "serverInfo": {
                            "name": "solver-mcp-server",
                            "version": "1.0.0"
                        }
                    }
                }
            
            elif method == "initialized":
                # No response needed for initialized notification
                return None
            
            elif method == "tools/list":
                tools = []
                for service_name in SOLVER_REGISTRY.keys():
                    tools.append({
                        "name": service_name,
                        "description": f"Execute {service_name} service via solver node",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "service": {
                                    "type": "string",
                                    "description": "The service to execute"
                                },
                                "data": {
                                    "type": "object",
                                    "description": "Data payload for the service"
                                }
                            },
                            "required": ["service"]
                        }
                    })
                
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "tools": tools
                    }
                }
            
            elif method == "tools/call":
                tool_name = params.get("name")
                tool_args = params.get("arguments", {})
                
                if tool_name not in SOLVER_REGISTRY:
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32601,
                            "message": f"Tool '{tool_name}' not found"
                        }
                    }
                
                solver_url = SOLVER_REGISTRY[tool_name]
                forward_url = f"{solver_url}/execute_rfd"
                
                # Prepare the RFD
                rfd = {
                    "service": tool_name,
                    **tool_args
                }
                
                logger.info(f"Forwarding RFD to solver at: {forward_url}")
                
                async with httpx.AsyncClient() as client:
                    try:
                        response = await client.post(forward_url, json=rfd, timeout=15.0)
                        response.raise_for_status()
                        result = response.json()
                        
                        return {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "result": {
                                "content": [
                                    {
                                        "type": "text",
                                        "text": json.dumps(result, indent=2)
                                    }
                                ]
                            }
                        }
                    
                    except httpx.RequestError as e:
                        logger.error(f"Failed to connect to solver: {e}")
                        return {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "error": {
                                "code": -32603,
                                "message": f"Could not connect to solver: {str(e)}"
                            }
                        }
                    except httpx.HTTPStatusError as e:
                        logger.error(f"Solver returned error: {e.response.status_code}")
                        return {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "error": {
                                "code": -32603,
                                "message": f"Solver error: {e.response.status_code} - {e.response.text}"
                            }
                        }
            
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Unknown method: {method}"
                    }
                }
        
        except Exception as e:
            logger.error(f"Unexpected error handling {method}: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
    
    async def run(self):
        """Run the MCP server using stdio"""
        logger.info("Starting MCP Server...")
        
        # Read from stdin line by line
        while True:
            try:
                line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
                if not line:
                    break
                
                line = line.strip()
                if not line:
                    continue
                
                logger.info(f"Received line: {line}")
                
                # Parse JSON-RPC request
                try:
                    request = json.loads(line)
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON: {e}")
                    continue
                
                # Handle the request
                response = await self.handle_request(request)
                
                # Send response if needed
                if response is not None:
                    response_json = json.dumps(response)
                    print(response_json, flush=True)
                    logger.info(f"Sent response: {response_json}")
            
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                break
        
        logger.info("MCP Server shutting down...")

async def main():
    """Main entry point"""
    server = MCPServer()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())