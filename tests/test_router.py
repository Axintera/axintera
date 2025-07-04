import pytest
from datasolver.providers.mcp.router import RFDRouter
from datasolver.providers.mcp.client import MCPClient
from datasolver.providers.mcp.tools.tool import MCPTool

# dummy tool
class EchoTool(MCPTool):
    def __init__(self): super().__init__("echo","returns echo")
    def validate_rfd(self,rfd): return rfd.get("service")=="echo"
    def generate(self,rfd,**k): return [{"echo": rfd.get("payload","hi")}]
    def cost(self,r): return 10

@pytest.fixture
def router():
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
