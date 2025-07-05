#!/usr/bin/env python3
"""
Fixed MCP Server for Amazon Q
This implements the MCP protocol over stdio with proper timeout handling
"""

import asyncio
import json
import logging
import sys
import signal
from typing import Any, Dict, List, Optional
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
        self.shutdown_event = asyncio.Event()
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.shutdown_event.set()
    
    async def handle_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
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
    
    async def read_stdin_with_timeout(self, timeout=1.0):
        """Read from stdin with timeout to prevent hanging"""
        try:
            # Use asyncio to read with timeout
            loop = asyncio.get_event_loop()
            future = loop.run_in_executor(None, sys.stdin.readline)
            line = await asyncio.wait_for(future, timeout=timeout)
            return line
        except asyncio.TimeoutError:
            return None
        except Exception as e:
            logger.error(f"Error reading stdin: {e}")
            return None
    
    async def run(self):
        """Run the MCP server using stdio with proper timeout handling"""
        logger.info("Starting MCP Server...")
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        try:
            while not self.shutdown_event.is_set():
                try:
                    # Read with timeout to prevent hanging
                    line = await self.read_stdin_with_timeout(timeout=1.0)
                    
                    if line is None:
                        # Timeout occurred, check if we should continue
                        continue
                    
                    if not line:  # EOF
                        logger.info("Received EOF, shutting down...")
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
                
                except KeyboardInterrupt:
                    logger.info("Received keyboard interrupt, shutting down...")
                    break
                except Exception as e:
                    logger.error(f"Error in main loop: {e}")
                    # Don't break on errors, keep the server running
                    continue
        
        except Exception as e:
            logger.error(f"Fatal error in server: {e}")
        finally:
            logger.info("MCP Server shutting down...")

async def main():
    """Main entry point"""
    server = MCPServer()
    await server.run()

if __name__ == "__main__":
    # Check if running in test mode
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        logger.info("Running in test mode - will exit after 10 seconds")
        async def test_run():
            server = MCPServer()
            try:
                await asyncio.wait_for(server.run(), timeout=10.0)
            except asyncio.TimeoutError:
                logger.info("Test timeout reached, exiting")
        asyncio.run(test_run())
    else:
        asyncio.run(main())
