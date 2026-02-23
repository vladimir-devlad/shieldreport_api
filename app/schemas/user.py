from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class RoleSimple(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class SupervisorSimple(BaseModel):
    id: int
    name: str
    last_name: str
    username: str

    class Config:
        from_attributes = True


class UserSimple(BaseModel):
    id: int
    name: str
    last_name: str
    username: str
    is_active: bool
    razon_sociales: Optional[List["RazonSocialSimple"]] = []

    class Config:
        from_attributes = True


class RazonSocialSimple(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


# necesario para resolver la referencia circular
UserSimple.model_rebuild()


class UserCreate(BaseModel):
    """Schema para crear un usuario"""

    name: str
    last_name: str
    username: str
    password: str
    role_id: int
    supervisor_id: Optional[int] = None
    razon_social_ids: Optional[List[int]] = []


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


class UserDetailResponse(UserResponse):
    """
    Respuesta completa según el rol:
    - usuario    → datos básicos + supervisor + razones sociales
    - supervisor → datos básicos + usuarios a cargo + razones sociales
    - admin      → datos básicos + rol + sin restricciones
    """

    id: int
    name: str
    last_name: str
    username: str
    is_active: bool
    role_id: int
    created_at: datetime
    updated_at: datetime
    role: RoleSimple
    supervisor: Optional[SupervisorSimple] = None  # a qué supervisor pertenece
    supervised_users: Optional[List[UserSimple]] = []  # qué usuarios tiene a cargo
    razon_sociales: Optional[List[RazonSocialSimple]] = []

    class Config:
        from_attributes = True
