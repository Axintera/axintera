"""
Very small stub so `import mcp_sdk` works in unit-tests.

Only functionality the tests need is the ability to hold a
`_tools` registry when the client is instantiated.
"""
class MCPClient:                       # pylint: disable=too-few-public-methods
    def __init__(self, *_, **__):
        self._tools = {}
    def register_tool(self, tool):
        self._tools[tool.name] = tool
