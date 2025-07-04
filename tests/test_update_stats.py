# tests/test_update_stats.py
"""
Unit-test for Axintera reputation counters.

• Uses a disposable SQLite file in the OS temp directory
  so it never touches your real state/stats.db.
• Verifies that `served` increments every call
  and `success` increments only when ok=True.
• Confirms the score column is created and defaults to 0.0.
"""
import tempfile, os, sqlite3, pathlib

import reputation  # ← your helper

def setup_function():
    """Run before each test – reset to a fresh empty DB."""
    # point DB_PATH at a temporary file
    reputation.DB_PATH = pathlib.Path(tempfile.gettempdir()) / "axintera_test_stats.db"
    if reputation.DB_PATH.exists():
        os.remove(reputation.DB_PATH)
    reputation.init_db()

def test_update_stats_counters():
    pid = "0xTEST"

    # 7 successes
    for _ in range(7):
        reputation.update_stats(pid, True)

    # 3 failures
    for _ in range(3):
        reputation.update_stats(pid, False)

    # inspect row
    with sqlite3.connect(reputation.DB_PATH) as conn:
        served, success, score = conn.execute(
            "SELECT served, success, score FROM providerstat WHERE provider_id=?",
            (pid.lower(),),
        ).fetchone()

    assert (served, success, score) == (10, 7, 0.0)
