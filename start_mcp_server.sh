#!/bin/bash
# Start the MCP server for the solver node

echo "Starting MCP Server for Solver Node..."
cd "$(dirname "$0")"
python stdio_mcp_server.py
