#!/usr/bin/env python3
"""
HTTP-based MCP Server for testing
"""

import json
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("HTTPMCPServer")

class MCPHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Handle MCP requests via HTTP POST"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            request = json.loads(post_data.decode('utf-8'))
            
            logger.info(f"Received request: {request.get('method', 'unknown')}")
            
            response = self.handle_mcp_request(request)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
            
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            self.send_response(500)
            self.end_headers()
    
    def handle_mcp_request(self, request):
        """Handle MCP protocol requests"""
        method = request.get("method")
        request_id = request.get("id")
        
        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "http-mcp-server", "version": "1.0.0"}
                }
            }
        elif method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {"tools": []}
            }
        elif method == "tools/call":
            # Mock tool call response
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [{"type": "text", "text": "Mock tool response"}]
                }
            }
        else:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32601, "message": f"Unknown method: {method}"}
            }
    
    def log_message(self, format, *args):
        """Override to use our logger"""
        logger.info(format % args)

def start_server(port=8000):
    """Start the HTTP MCP server"""
    server = HTTPServer(('localhost', port), MCPHandler)
    logger.info(f"Starting HTTP MCP Server on port {port}")
    server.serve_forever()

if __name__ == "__main__":
    start_server()
