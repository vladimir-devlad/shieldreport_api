from typing import List

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_admin
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.services import user_service

router = APIRouter(prefix="/users", tags=["Usuarios"])


@router.get("/", response_model=List[UserResponse])
def list_users(
    db: Session = Depends(get_db), current_user: User = Depends(require_admin)
):
    """Lista todos los usuarios — solo admin"""
    return user_service.get_all_users(db)


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Obtiene un usuario por ID — solo admin"""
    return user_service.get_user_by_id(user_id, db)


@router.post("/", response_model=UserResponse, status_code=201)
def create_user(
    request: Request,
    body: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Crea un nuevo usuario — solo admin"""
    ip = request.client.host
    return user_service.create_user(body, db, current_user.id, ip)


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    request: Request,
    body: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Actualiza un usuario — solo admin"""
    ip = request.client.host
    return user_service.update_user(user_id, body, db, current_user.id, ip)


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Desactiva un usuario — solo admin"""
    ip = request.client.host
    return user_service.delete_user(user_id, db, current_user.id, ip)
