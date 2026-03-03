from datetime import datetime

from pydantic import BaseModel


class SyncLogResponse(BaseModel):
    id: int
    table_name: str
    last_updated: datetime
    operation: str

    class Config:
        from_attributes = True
