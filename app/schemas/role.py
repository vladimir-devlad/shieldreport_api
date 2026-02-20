from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class RoleCreate(BaseModel):
    name: str
    description: Optional[str] = None


class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class RoleResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
