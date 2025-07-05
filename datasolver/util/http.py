# datasolver/util/http.py
import httpx, functools, logging

log = logging.getLogger("http")

@functools.cache
def _client() -> httpx.Client:
    return httpx.Client(timeout=10)

def get(url: str, **kw):
    log.info(f"HTTP GET {url}")
    r = _client().get(url, **kw)
    r.raise_for_status()
    return r.json()
