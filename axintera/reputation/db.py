from pathlib import Path
from sqlmodel import SQLModel, create_engine

DB_PATH = Path(__file__).resolve().parents[2] / "state" / "axintera_stats.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(
    f"sqlite:///{DB_PATH}",
    echo=False,
    connect_args={"check_same_thread": False},
)

def init_db() -> None:
    from .models import ProviderStat        # local import avoids circular refs
    SQLModel.metadata.create_all(engine)
