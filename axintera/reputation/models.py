from sqlmodel import SQLModel, Field
from datetime import datetime

class ProviderStat(SQLModel, table=True):
    provider_id: str = Field(primary_key=True)
    served: int = 0
    success: int = 0
    score: float = 0.0
    updated_at: datetime = Field(default_factory=datetime.utcnow)
