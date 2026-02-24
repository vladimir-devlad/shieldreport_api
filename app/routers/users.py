from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import (
    get_current_user,
    require_admin,
    require_admin_or_supervisor,
)
from app.models.user import User
from app.schemas.user import UserCreate, UserDetailResponse, UserUpdate
from app.services import user_service

router = APIRouter(prefix="/users", tags=["Usuarios"])


class ChangePasswordRequest(BaseModel):
    new_password: str


@router.get("/", response_model=List[UserDetailResponse])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_supervisor),
):
    """Admin ve todos — Supervisor ve solo su grupo"""
    return user_service.get_all_users(db, current_user)


@router.get("/me", response_model=UserDetailResponse)
def my_profile(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """Mi propio perfil — todos los roles"""
    return user_service.get_my_profile(db, current_user)


@router.get("/sin-supervisor")
def users_sin_supervisor(
    search: Optional[str] = Query(None, description="Buscar por nombre o username"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_supervisor),
):
    """Lista usuarios sin supervisor — paginado con búsqueda"""
    return user_service.get_users_sin_supervisor(db, current_user, search, page, limit)


@router.get("/{user_id}", response_model=UserDetailResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_supervisor),
):
    """Admin ve cualquiera — Supervisor solo los suyos"""
    return user_service.get_user_by_id(user_id, db, current_user)


@router.post("/", response_model=UserDetailResponse, status_code=201)
def create_user(
    request: Request,
    body: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Solo admin puede crear usuarios"""
    return user_service.create_user(body, db, current_user, request.client.host)


@router.put("/me/password")
def change_my_password(
    body: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cambiar mi propia contraseña — todos los roles"""
    return user_service.change_my_password(body.new_password, db, current_user)


@router.put("/{user_id}", response_model=UserDetailResponse)
def update_user(
    user_id: int,
    request: Request,
    body: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Solo admin puede editar usuarios"""
    return user_service.update_user(
        user_id, body, db, current_user, request.client.host
    )


@router.delete("/{user_id}")
def deactivate_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Solo admin puede desactivar usuarios"""
    return user_service.deactivate_user(user_id, db, current_user, request.client.host)
