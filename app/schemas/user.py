import re
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, field_validator


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


UserSimple.model_rebuild()


class EmailItem(BaseModel):
    email: EmailStr

    class Config:
        from_attributes = True


class PhoneItem(BaseModel):
    phone_number: str

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, v):
        # acepta formato Perú (+519XXXXXXXX) e internacional (+[código][número])
        pattern = r"^\+?[1-9]\d{6,14}$"
        if not re.match(pattern, v.replace(" ", "").replace("-", "")):
            raise ValueError(
                "Formato de teléfono inválido. Ejemplo: +51987654321 o +1234567890"
            )
        return v

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    name: str
    middle_name: Optional[str] = None
    last_name: str
    second_last_name: Optional[str] = None
    password: Optional[str] = None
    role_id: int
    supervisor_id: Optional[int] = None
    razon_social_ids: Optional[List[int]] = []
    emails: Optional[List[EmailStr]] = []
    phones: Optional[List[str]] = []


class UserUpdate(BaseModel):
    name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    second_last_name: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    role_id: Optional[int] = None
    is_active: Optional[bool] = None
    emails: Optional[List[EmailStr]] = None
    phones: Optional[List[str]] = None


class UserResponse(BaseModel):
    id: int
    name: str
    middle_name: Optional[str]
    last_name: str
    second_last_name: Optional[str]
    username: str
    is_active: bool
    role_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserDetailResponse(BaseModel):
    id: int
    name: str
    middle_name: Optional[str]
    last_name: str
    second_last_name: Optional[str]
    username: str
    is_active: bool
    role_id: int
    created_at: datetime
    updated_at: datetime
    role: RoleSimple
    supervisor: Optional[SupervisorSimple] = None
    supervised_users: Optional[List[UserSimple]] = []
    razon_sociales: Optional[List[RazonSocialSimple]] = []
    emails: Optional[List[EmailItem]] = []
    phones: Optional[List[PhoneItem]] = []

    class Config:
        from_attributes = True
