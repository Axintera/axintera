#!/usr/bin/env python3
"""
Standard MCP Server using stdio (JSON-RPC over stdin/stdout)
This is the correct format for MCP servers
"""

import json
import sys
import logging
from typing import Dict, Any

# Set up logging to stderr so it doesn't interfere with JSON-RPC
logging.basicConfig(level=logging.INFO, stream=sys.stderr, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("MCPServer")

class MCPServer:
    def __init__(self):
        self.initialized = False
        logger.info("MCP Server starting...")
    
    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP requests"""
        method = request.get("method")
        request_id = request.get("id")
        params = request.get("params", {})
        
        logger.info(f"Handling method: {method}")
        
        try:
            if method == "initialize":
                return self.handle_initialize(request_id, params)
            elif method == "initialized":
                return self.handle_initialized(request_id)
            elif method == "tools/list":
                return self.handle_tools_list(request_id)
            elif method == "tools/call":
                return self.handle_tools_call(request_id, params)
            elif method == "resources/list":
                return self.handle_resources_list(request_id)
            elif method == "prompts/list":
                return self.handle_prompts_list(request_id)
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
        except Exception as e:
            logger.error(f"Error handling {method}: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
    
    def handle_initialize(self, request_id: int, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle initialize request"""
        self.initialized = True
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {},
                    "resources": {},
                    "prompts": {}
                },
                "serverInfo": {
                    "name": "solver-node-mcp",
                    "version": "1.0.0"
                }
            }
        }
    
    def handle_initialized(self, request_id: int) -> None:
        """Handle initialized notification (no response needed)"""
        logger.info("Client confirmed initialization")
        return None
    
    def handle_tools_list(self, request_id: int) -> Dict[str, Any]:
        """List available tools"""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "tools": [
                    {
                        "name": "generate_data",
                        "description": "Generate synthetic data based on schema",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "schema": {"type": "object"},
                                "count": {"type": "integer", "default": 10}
                            },
                            "required": ["schema"]
                        }
                    },
                    {
                        "name": "query_data",
                        "description": "Query existing data",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "query": {"type": "string"},
                                "table": {"type": "string"}
                            },
                            "required": ["query"]
                        }
                    }
                ]
            }
        }
    
    def handle_tools_call(self, request_id: int, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tool calls"""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if tool_name == "generate_data":
            return self.generate_data(request_id, arguments)
        elif tool_name == "query_data":
            return self.query_data(request_id, arguments)
        else:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32602,
                    "message": f"Unknown tool: {tool_name}"
                }
            }
    
    def generate_data(self, request_id: int, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Generate synthetic data"""
        schema = arguments.get("schema", {})
        count = arguments.get("count", 10)
        
        # Mock data generation
        mock_data = []
        for i in range(count):
            mock_record = {"id": i, "generated": True}
            # Add fields based on schema
            if "properties" in schema:
                for prop, prop_schema in schema["properties"].items():
                    if prop_schema.get("type") == "string":
                        mock_record[prop] = f"sample_{prop}_{i}"
                    elif prop_schema.get("type") == "number":
                        mock_record[prop] = i * 10.5
                    elif prop_schema.get("type") == "integer":
                        mock_record[prop] = i
                    elif prop_schema.get("type") == "boolean":
                        mock_record[prop] = i % 2 == 0
            mock_data.append(mock_record)
        
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": f"Generated {count} records based on schema"
                    },
                    {
                        "type": "resource",
                        "resource": {
                            "uri": "data://generated",
                            "mimeType": "application/json",
                            "text": json.dumps(mock_data, indent=2)
                        }
                    }
                ]
            }
        }
    
    def query_data(self, request_id: int, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Query data"""
        query = arguments.get("query", "")
        table = arguments.get("table", "default")
        
        # Mock query response
        mock_results = [
            {"id": 1, "name": "Sample Record 1", "value": 100},
            {"id": 2, "name": "Sample Record 2", "value": 200}
        ]
        
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": f"Query executed: {query} on table: {table}"
                    },
                    {
                        "type": "resource",
                        "resource": {
                            "uri": f"data://{table}",
                            "mimeType": "application/json",
                            "text": json.dumps(mock_results, indent=2)
                        }
                    }
                ]
            }
        }
    
    def handle_resources_list(self, request_id: int) -> Dict[str, Any]:
        """List available resources"""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "resources": []
            }
        }
    
    def handle_prompts_list(self, request_id: int) -> Dict[str, Any]:
        """List available prompts"""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "prompts": []
            }
        }
    
    def run(self):
        """Main server loop"""
        logger.info("MCP Server ready and listening on stdin...")
        
        try:
            while True:
                line = sys.stdin.readline()
                if not line:  # EOF
                    logger.info("EOF received, shutting down")
                    break
                
                line = line.strip()
                if not line:
                    continue
                
                try:
                    request = json.loads(line)
                    response = self.handle_request(request)
                    
                    if response is not None:  # Some methods don't return responses
                        print(json.dumps(response), flush=True)
                        
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON received: {e}")
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {
                            "code": -32700,
                            "message": "Parse error"
                        }
                    }
                    print(json.dumps(error_response), flush=True)
                    
        except KeyboardInterrupt:
            logger.info("Received interrupt, shutting down")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")

if __name__ == "__main__":
    server = MCPServer()
    server.run()
