from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class RazonSocialCreate(BaseModel):
    name: str


class RazonSocialUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None


class RazonSocialResponse(BaseModel):
    id: int
    name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RazonSocialDetailResponse(BaseModel):
    """Respuesta detallada con usuarios asignados — solo admin"""

    id: int
    name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    usuarios: Optional[List[dict]] = []

    class Config:
        from_attributes = True


class AssignRazonSocial(BaseModel):
    """Para asignar razones sociales a un usuario"""

    user_id: int
    razon_social_ids: List[int]
