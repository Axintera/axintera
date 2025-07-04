"""
reputation.py – Axintera lightweight telemetry
Creates/updates   state/stats.db

Table:
  provider_id TEXT PK
  served      INT
  success     INT
  score       REAL   (Wilson lower-bound, 0-1)
"""

import sqlite3, threading, math, asyncio
from pathlib import Path

# ─── paths & locks ────────────────────────────────────────────────────
DB_PATH = Path(__file__).resolve().parent / "state" / "stats.db"
_LOCK   = threading.Lock()

# ─── bootstrap ───────────────────────────────────────────────────────
def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _LOCK, sqlite3.connect(DB_PATH) as c:
        c.execute(
            "CREATE TABLE IF NOT EXISTS providerstat ("
            " provider_id TEXT PRIMARY KEY,"
            " served      INTEGER DEFAULT 0,"
            " success     INTEGER DEFAULT 0,"
            " score       REAL    DEFAULT 0)"
        )
        c.commit()

init_db()           # run once on import

# ─── counter helper ──────────────────────────────────────────────────
def update_stats(provider_id: str, ok: bool) -> None:
    """
    +1 to served; +1 to success if ok.
    Inserts (score = 0) on first sight.
    """
    with _LOCK, sqlite3.connect(DB_PATH) as c:
        c.execute(
            """
            INSERT INTO providerstat (provider_id, served, success, score)
            VALUES (?, 1, ?, 0)
            ON CONFLICT(provider_id) DO UPDATE SET
              served  = served  + 1,
              success = success + ?
            """,
            (provider_id.lower(), int(ok), int(ok)),
        )
        c.commit()

# ─── scoring helpers ────────────────────────────────────────────────
def wilson(success: int, served: int, z: float = 1.96) -> float:
    """95 % Wilson lower-bound."""
    if served == 0:
        return 0.0
    phat  = success / served
    denom = 1 + z**2 / served
    centre = phat + z**2 / (2 * served)
    adj   = z * math.sqrt((phat * (1 - phat) + z**2 / (4 * served)) / served)
    return round((centre - adj) / denom, 4)

async def hourly_recalc() -> None:
    """Recompute score for every provider once per hour."""
    while True:
        with _LOCK, sqlite3.connect(DB_PATH) as c:
            rows = c.execute(
                "SELECT provider_id, served, success FROM providerstat"
            ).fetchall()
            for pid, served, success in rows:
                score = wilson(success, served)
                c.execute(
                    "UPDATE providerstat SET score=? WHERE provider_id=?",
                    (score, pid),
                )
            c.commit()
        await asyncio.sleep(3600)          # lower during demos if you like
