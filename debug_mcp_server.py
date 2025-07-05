#!/usr/bin/env python3
import asyncio
import json
import sys
import logging

# Setup logging to stderr
logging.basicConfig(level=logging.INFO, stream=sys.stderr, format='%(levelname)s: %(message)s')
logger = logging.getLogger("DebugMCP")

async def main():
    logger.info("DEBUG: MCP Server starting...")
    
    try:
        while True:
            # Read a line from stdin
            line = sys.stdin.readline()
            if not line:
                logger.info("DEBUG: EOF received, shutting down")
                break
            
            line = line.strip()
            if not line:
                continue
            
            logger.info(f"DEBUG: Received line: {line}")
            
            try:
                request = json.loads(line)
                method = request.get("method")
                request_id = request.get("id")
                
                logger.info(f"DEBUG: Processing method: {method}")
                
                if method == "initialize":
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {
                            "protocolVersion": "2024-11-05",
                            "capabilities": {"tools": {}},
                            "serverInfo": {"name": "debug-mcp", "version": "1.0.0"}
                        }
                    }
                    response_json = json.dumps(response)
                    print(response_json, flush=True)
                    logger.info(f"DEBUG: Sent response: {response_json}")
                
                elif method == "tools/list":
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {"tools": []}
                    }
                    response_json = json.dumps(response)
                    print(response_json, flush=True)
                    logger.info(f"DEBUG: Sent tools/list response")
                    
            except json.JSONDecodeError as e:
                logger.error(f"DEBUG: JSON decode error: {e}")
            except Exception as e:
                logger.error(f"DEBUG: Error processing request: {e}")
                
    except Exception as e:
        logger.error(f"DEBUG: Fatal error: {e}")
    finally:
        logger.info("DEBUG: MCP Server shutting down...")

if __name__ == "__main__":
    asyncio.run(main())
