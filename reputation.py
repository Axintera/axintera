import sqlite3, threading, os
from pathlib import Path

DB_PATH = Path(__file__).parent / "state" / "stats.db"
_LOCK   = threading.Lock()

def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _LOCK, sqlite3.connect(DB_PATH) as c:
        c.execute(
            "CREATE TABLE IF NOT EXISTS providerstat ("
            " provider_id TEXT PRIMARY KEY,"
            " served INTEGER DEFAULT 0,"
            " success INTEGER DEFAULT 0)"
        )
        c.commit()

def update_stats(pid: str, ok: bool):
    init_db()
    with _LOCK, sqlite3.connect(DB_PATH) as c:
        c.execute(
            "INSERT INTO providerstat VALUES (?,1,?) "
            "ON CONFLICT(provider_id) DO UPDATE SET "
            "served  = served  + 1,"
            "success = success + ?",
            (pid, int(ok), int(ok)),
        )
        c.commit()
