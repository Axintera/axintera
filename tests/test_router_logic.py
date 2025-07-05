# tests/test_router_logic.py
import pytest
from datasolver.providers.mcp.router import RFDRouter
from datasolver.providers.mcp.client import MCPClient
from datasolver.providers.mcp.tools.tool import MCPTool

# --- Setup Dummy Tools for Testing ---
# FIX: Give each tool a unique name to avoid dictionary key collision
class CheapTool(MCPTool):
    @property
    def name(self): return "cheap_tool_service"
    @property
    def description(self): return "The cheap version"
    @property
    def capabilities(self): return {}
    # FIX: Validate based on a generic 'task' instead of a conflicting 'service' name
    def validate_rfd(self, rfd): return rfd.get("task") == "shared_task"
    def generate_data(self, rfd): return [{"provider": "cheap"}]
    def generate(self, rfd, **kwargs): return self.generate_data(rfd)
    def cost(self, rfd): return 10.0

class ExpensiveTool(MCPTool):
    @property
    def name(self): return "expensive_tool_service"
    @property
    def description(self): return "The expensive version"
    @property
    def capabilities(self): return {}
    def validate_rfd(self, rfd): return rfd.get("task") == "shared_task"
    def generate_data(self, rfd): return [{"provider": "expensive"}]
    def generate(self, rfd, **kwargs): return self.generate_data(rfd)
    def cost(self, rfd): return 100.0

# --- Tests ---

def test_router_chooses_cheapest_tool():
    """
    Why: Proves the core 'cost-based routing' feature works.
    How: Registers two tools that can handle the same task but have different costs.
    """
    # The MCPClient will be initialized in offline mode as MCP_SERVER_URL is not set in tests
    mcp = MCPClient(tools=[CheapTool, ExpensiveTool])
    router = RFDRouter(mcp)
    
    # FIX: Use the generic 'task' key for the RFD
    rfd = {"task": "shared_task"}
    result = router.fulfil(rfd)
    
    # FIX: The router should have picked the tool with the lower cost. Assert its actual name.
    assert result["tool"] == "cheap_tool_service"
    assert result["records"] == [{"provider": "cheap"}]


def test_router_raises_error_if_no_tool_found():
    """
    Why: Ensures the solver fails gracefully if it can't handle a request.
    How: Initializes a router with a tool, but sends an RFD for a different service.
    """
    mcp = MCPClient(tools=[CheapTool])
    router = RFDRouter(mcp)
    
    rfd_unfulfillable = {"task": "some_other_task"}
    
    with pytest.raises(RuntimeError, match="No tool can satisfy RFD"):
        router.fulfil(rfd_unfulfillable)


@pytest.mark.parametrize("merge_mode, expected_result", [
    ("concat", [{"id": 1}, {"id": 2}, {"id": 2}, {"id": 3}]),
    ("union", [{"id": 1}, {"id": 2}, {"id": 2}, {"id": 3}]),
    ("intersection", [{"id": 2}]),
])
def test_router_merge_logic(merge_mode, expected_result):
    """
    Why: Tests the different data aggregation strategies with dictionaries.
    How: Directly calls the private _merge method with sample data.
    """
    mcp = MCPClient(tools=[])
    router = RFDRouter(mcp)
    
    chunk1_dicts = [{"id": 1}, {"id": 2}]
    chunk2_dicts = [{"id": 2}, {"id": 3}]
    
    merged = router._merge([chunk1_dicts, chunk2_dicts], merge_mode)
    
    # Sort both lists by 'id' to ensure a consistent order for comparison
    merged_sorted = sorted(merged, key=lambda d: d['id'])
    expected_sorted = sorted(expected_result, key=lambda d: d['id'])
    
    assert merged_sorted == expected_sorted