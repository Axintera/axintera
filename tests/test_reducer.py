from datasolver.providers.mcp.tools.reducer import ReduceAvgTool

def test_avg():
    tool = ReduceAvgTool()
    rfd = {"service":"reduce_avg",
           "records":[{"x":1,"y":2},{"x":3,"y":4}]}
    assert tool.generate(rfd) == [{"x":2,"y":3}]
