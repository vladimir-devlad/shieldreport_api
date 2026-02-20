from typing import List

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_admin
from app.models.user import User
from app.schemas.role import RoleCreate, RoleResponse, RoleUpdate
from app.services import role_service

router = APIRouter(prefix="/roles", tags=["Roles"])


@router.get("/", response_model=List[RoleResponse])
def list_roles(
    db: Session = Depends(get_db), current_user: User = Depends(require_admin)
):
    """Lista todos los roles — solo admin"""
    return role_service.get_all_roles(db)


@router.get("/{role_id}", response_model=RoleResponse)
def get_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Obtiene un rol por ID — solo admin"""
    return role_service.get_role_by_id(role_id, db)


@router.post("/", response_model=RoleResponse, status_code=201)
def create_role(
    request: Request,
    body: RoleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Crea un nuevo rol — solo admin"""
    ip = request.client.host
    return role_service.create_role(body, db, current_user.id, ip)


@router.put("/{role_id}", response_model=RoleResponse)
def update_role(
    role_id: int,
    request: Request,
    body: RoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Edita un rol — solo admin"""
    ip = request.client.host
    return role_service.update_role(role_id, body, db, current_user.id, ip)


@router.delete("/{role_id}")
def delete_role(
    role_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Elimina un rol — solo admin"""
    ip = request.client.host
    return role_service.delete_role(role_id, db, current_user.id, ip)
