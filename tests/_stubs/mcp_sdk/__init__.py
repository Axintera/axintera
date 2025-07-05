"""Ultra-minimal stub so `import mcp_sdk` succeeds in unit-tests."""
class MCPClient:                       # pylint: disable=too-few-public-methods
    def __init__(self, *_, **__):
        self._tools = {}
    def register_tool(self, tool):
        self._tools[tool.name] = tool
