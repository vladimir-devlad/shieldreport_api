from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class UserCreate(BaseModel):
    """Schema para crear un usuario"""

    name: str
    last_name: str
    username: str
    password: str
    role_id: int


class UserUpdate(BaseModel):
    """Schema para actualizar un usuario (todos opcionales)"""

    name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    role_id: Optional[int] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    """Lo que el API devuelve al consultar un usuario (sin password)"""

    id: int
    name: str
    last_name: str
    username: str
    is_active: bool
    role_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
