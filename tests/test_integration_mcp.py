# tests/test_integration_mcp.py
import subprocess, time, json, requests, os, signal, pathlib

RFD = json.loads(pathlib.Path("examples/rfd_yield_matrix_eth_usdc.json").read_text())

def wait_on(url: str, tries: int = 25, delay: float = 0.3):
    for _ in range(tries):
        try:
            requests.get(url, timeout=0.25); return
        except Exception:
            time.sleep(delay)
    raise RuntimeError(f"{url} never came up")

def test_e2e_yield_matrix(tmp_path):
    # ── 1 ▸ start mock MCP server on 8000 ─────────────────────────
    srv = subprocess.Popen(
        ["uvicorn", "mock_mcp_server:app", "--port", "8000"],
        stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT,
    )
    wait_on("http://localhost:8000/docs")

    # ── 2 ▸ start solver node on 8001 ─────────────────────────────
    env = {
        **os.environ,
        "MCP_SERVER_URL": "http://localhost:8000",
        "SOLVER_PORT":     "8001",
        "SOLVER_URL":     "http://localhost:8001",
    }
    sol = subprocess.Popen(
        ["python", "solverNode.py"], env=env,
        stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT,
    )
    wait_on("http://localhost:8001/healthz")
   
    # ── 3 ▸ fire RFD through MCP server ───────────────────────────
    resp = requests.post("http://localhost:8000/fulfill", json=RFD, timeout=5)
    data = resp.json()
    assert resp.status_code == 200
    assert "records" in data and "rows" in data["records"]
    assert isinstance(data["records"]["rows"], list)
    assert {"protocol", "apy", "risk"} <= data["records"]["rows"][0].keys()

    # ── 4 ▸ clean shutdown ────────────────────────────────────────
    for p in (sol, srv):
        p.send_signal(signal.SIGTERM)
        p.wait(timeout=5)
