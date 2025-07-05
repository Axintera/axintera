import os
import logging
from typing import Dict, Any, Optional, List, Type

from .provider import MCPProvider
from .tools.tool import MCPTool

logger = logging.getLogger('MCPClient')

class MCPClient(MCPProvider):
    """MCP client for data generation.
    Supports both online (real SDK) and offline (test/stub) modes.
    """
    
    def __init__(self, tools: Optional[List[Type[MCPTool]]] = None):
        """Initialize MCP client
        
        Args:
            tools: List of MCP tool classes to register (optional)
        """
        super().__init__()
        self._tools = {}
        # This client object will either be the real SDK client or a simple stub
        self.client = None 
        self._initialize_client(tools or [])
    
    def _initialize_client(self, tool_classes: List[Type[MCPTool]]):
        """Initialize MCP client with tools.
        
        If MCP_SERVER_URL is set, it initializes the real SDK.
        Otherwise, it falls back to an offline stub for testing purposes.
        """
        server_url = os.getenv("MCP_SERVER_URL")

        if not server_url:
            logger.info("MCP_SERVER_URL not set. Initializing in OFFLINE/TEST mode.")
            # Use the simple stub/shim for local tests
            from mcp_sdk import MCPClient as StubClient
            self.client = StubClient()
        else:
            # Original logic for production/online mode
            logger.info(f"MCP_SERVER_URL found. Initializing in ONLINE mode for {server_url}.")
            try:
                from mcp_sdk import MCPClient as SDKClient
                
                server_config = {
                    "timeout": int(os.getenv("MCP_SERVER_TIMEOUT", "30")),
                    "retries": int(os.getenv("MCP_SERVER_RETRIES", "3")),
                    "api_key": os.getenv("MCP_SERVER_API_KEY"),
                    "verify_ssl": os.getenv("MCP_SERVER_VERIFY_SSL", "true").lower() == "true"
                }
                
                self.client = SDKClient(server_url, **server_config)
            except ImportError:
                logger.error("MCP SDK not installed for online mode. Install with: pip install mcp-sdk")
                raise
            except Exception as e:
                logger.error(f"Failed to initialize ONLINE MCP client: {e}")
                raise

        # This registration logic now works for both the real client and the stub
        for tool_class in tool_classes:
            # Instantiate the tool
            tool_instance = tool_class() 
            self.register_tool(tool_instance)

        if not self._tools:
            logger.warning("No MCP tools registered")
    
    def register_tool(self, tool: MCPTool):
        """Register a new MCP tool with both the local registry and the client.
        
        Args:
            tool: MCP tool instance to register
        """
        if not hasattr(self, '_tools'):
             self._tools = {}

        if not self.client:
             # This can happen if called before __init__ is complete
             from mcp_sdk import MCPClient as StubClient
             self.client = StubClient()

        self._tools[tool.name] = tool
        if self.client:
            self.client.register_tool(tool)
        logger.info(f"Registered MCP tool: {tool.name}")
    
    def get_tool(self, tool_name: str) -> Optional[MCPTool]:
        """Get tool by name
        
        Args:
            tool_name: Name of tool to get
            
        Returns:
            Tool instance if found
        """
        return self._tools.get(tool_name)
    
    def list_tools(self) -> List[str]:
        """List available tools
        
        Returns:
            List of tool names
        """
        return list(self._tools.keys())
    
    def generate_dataset(self, rfd: Dict) -> Dict[str, Any]:
        """Generate dataset using MCP tools"""
        pass