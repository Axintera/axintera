from sqlmodel import Session
from .db import engine
from .models import ProviderStat

def update_stats(provider_id: str, ok: bool) -> None:
    """Add 1 to served; add 1 to success if ok=True."""
    with Session(engine) as s:
        row = s.get(ProviderStat, provider_id) or ProviderStat(provider_id=provider_id)
        row.served  += 1
        row.success += int(ok)
        s.add(row)
        s.commit()
