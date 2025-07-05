import pytest
from datasolver.providers.mcp.router import RFDRouter
from datasolver.providers.mcp.client import MCPClient
from datasolver.providers.mcp.tools.tool import MCPTool

# Fully implement the abstract methods from MCPTool
class EchoTool(MCPTool):
    @property
    def name(self) -> str:
        return "echo"

    @property
    def description(self) -> str:
        return "A simple tool that returns its input payload."

    @property
    def capabilities(self) -> dict:
        return {"input": "Any JSON with a 'payload' key", "output": "The payload value"}
    
    def validate_rfd(self, rfd: dict) -> bool:
        return rfd.get("service") == self.name

    def generate_data(self, rfd: dict) -> list:
        return [{"echo": rfd.get("payload", "hi")}]

    # The router directly calls a 'generate' method on the tool
    def generate(self, rfd: dict, **kwargs) -> list:
        return self.generate_data(rfd)

    def cost(self, rfd: dict) -> float:
        return 10

@pytest.fixture
def router():
    # MCPClient now handles offline mode correctly without needing env vars
    mcp = MCPClient(tools=[EchoTool])
    return RFDRouter(mcp)

def test_single(router):
    rfd = {"service":"echo","payload":"ping"}
    out = router.fulfil(rfd)
    assert out["records"] == [{"echo":"ping"}]

def test_chain(router):
    child = {"service":"echo","payload":"child"}
    root  = {"service":"echo","payload":"root",
             "dependencies":[child],"aggregation":"concat"}
    recs = router.fulfil(root)["records"]
    assert recs == [{"echo":"child"},{"echo":"root"}]