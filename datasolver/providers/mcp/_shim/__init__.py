"""
Minimal stub that satisfies `from mcp_sdk import MCPClient`
when the real SDK is not installed (e.g. during local tests).
"""

class MCPClient:                      # noqa: N801
    def __init__(self, *_, **__):
        pass

    # no-op register (router tests only need this)
    def register_tool(self, tool):
        setattr(self, f"_tool_{tool.name}", tool)
