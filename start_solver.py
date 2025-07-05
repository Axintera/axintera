#!/usr/bin/env python3
"""
Solver Node Startup Script
Handles different modes and prevents hanging
"""

import argparse
import asyncio
import logging
import sys
import os
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SolverStartup")

def main():
    parser = argparse.ArgumentParser(description="Start Reppo Solver Node")
    parser.add_argument("--mode", choices=["mcp", "standalone", "test"], default="standalone",
                       help="Mode to run the solver in")
    parser.add_argument("--test", action="store_true", help="Run in test mode")
    parser.add_argument("--mock", action="store_true", help="Run in mock mode")
    parser.add_argument("--timeout", type=int, default=30, help="Timeout in seconds for test mode")
    
    args = parser.parse_args()
    
    if args.mode == "mcp":
        logger.info("Starting MCP server mode...")
        from fixed_mcp_server import main as mcp_main
        
        if args.test:
            logger.info(f"Running MCP server in test mode (timeout: {args.timeout}s)")
            async def test_mcp():
                from fixed_mcp_server import MCPServer
                server = MCPServer()
                try:
                    await asyncio.wait_for(server.run(), timeout=args.timeout)
                except asyncio.TimeoutError:
                    logger.info("Test timeout reached, exiting")
            asyncio.run(test_mcp())
        else:
            asyncio.run(mcp_main())
    
    elif args.mode == "standalone":
        logger.info("Starting standalone solver node...")
        
        # Import the original main function
        try:
            from main import main as original_main
            # Set up sys.argv for the original main function
            sys.argv = ["main.py", "start"]
            if args.test:
                sys.argv.append("--test")
            if args.mock:
                sys.argv.append("--mock")
            
            original_main()
        except ImportError:
            logger.error("Could not import original main function")
            sys.exit(1)
    
    elif args.mode == "test":
        logger.info("Running comprehensive test...")
        
        # Run the MCP server test
        from test_mcp_server import test_mcp_server
        test_mcp_server()
        
        # Run the solver node test if available
        try:
            from main import main as original_main
            sys.argv = ["main.py", "start", "--test"]
            original_main()
        except Exception as e:
            logger.error(f"Solver node test failed: {e}")

if __name__ == "__main__":
    main()
