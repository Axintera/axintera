"""
Axintera root package
Exports:
   init_db()  – create tables on boot
"""
from .reputation.db import init_db   # re-export
__all__ = ["init_db"]
