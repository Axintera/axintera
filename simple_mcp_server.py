#!/usr/bin/env python3
"""
Simple MCP Server that doesn't hang
"""

import json
import sys
import select
import logging

logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger("SimpleMCP")

def handle_request(request):
    """Handle MCP requests"""
    method = request.get("method")
    request_id = request.get("id")
    
    logger.info(f"Handling: {method}")
    
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "simple-mcp", "version": "1.0.0"}
            }
        }
    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {"tools": []}
        }
    else:
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": -32601, "message": f"Unknown method: {method}"}
        }

def main():
    logger.info("Starting Simple MCP Server...")
    
    try:
        while True:
            # Check if input is available (non-blocking)
            if select.select([sys.stdin], [], [], 1.0)[0]:
                line = sys.stdin.readline()
                if not line:  # EOF
                    break
                
                line = line.strip()
                if not line:
                    continue
                
                try:
                    request = json.loads(line)
                    response = handle_request(request)
                    if response:
                        print(json.dumps(response), flush=True)
                except json.JSONDecodeError:
                    logger.error("Invalid JSON received")
            else:
                # No input available, continue (prevents hanging)
                logger.debug("No input available, continuing...")
                
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    main()
