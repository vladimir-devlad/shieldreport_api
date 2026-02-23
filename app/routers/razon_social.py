from typing import List

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import (
    get_current_user,
    require_superadmin,
    require_superadmin_or_admin,
)
from app.models.user import User
from app.schemas.razon_social import (
    AssignRazonSocial,
    RazonSocialCreate,
    RazonSocialResponse,
    RazonSocialUpdate,
)
from app.services import razon_social_service

router = APIRouter(prefix="/razon-social", tags=["Razón Social"])


@router.get("/", response_model=List[RazonSocialResponse])
def list_razon_social(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """
    Superadmin → todas (activas e inactivas)
    Admin      → solo activas
    Supervisor/Usuario → solo las suyas activas
    """
    return razon_social_service.get_all(db, current_user)


@router.get("/user/{user_id}", response_model=List[RazonSocialResponse])
def get_user_razon_social(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_superadmin_or_admin),
):
    """Ver razones sociales de un usuario — superadmin y admin"""
    return razon_social_service.get_by_user(user_id, db, current_user)


@router.post("/", response_model=RazonSocialResponse, status_code=201)
def create_razon_social(
    request: Request,
    body: RazonSocialCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_superadmin),
):
    """Crear razón social — solo superadmin"""
    return razon_social_service.create(body, db, current_user.id, request.client.host)


@router.put("/{razon_social_id}", response_model=RazonSocialResponse)
def update_razon_social(
    razon_social_id: int,
    request: Request,
    body: RazonSocialUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_superadmin),
):
    """Editar razón social — solo superadmin"""
    return razon_social_service.update(
        razon_social_id, body, db, current_user.id, request.client.host
    )


@router.patch(
    "/{razon_social_id}/toggle",
)
def toggle_razon_social(
    razon_social_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_superadmin),
):
    """Activar o desactivar razón social — solo superadmin"""
    return razon_social_service.toggle_active(
        razon_social_id, db, current_user.id, request.client.host
    )


@router.delete("/{razon_social_id}")
def delete_razon_social(
    razon_social_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_superadmin),
):
    """Eliminar razón social — solo superadmin"""
    return razon_social_service.delete(
        razon_social_id, db, current_user.id, request.client.host
    )


@router.post("/assign")
def assign_razon_social(
    request: Request,
    body: AssignRazonSocial,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Superadmin → asigna cualquier RS a cualquier usuario
    Admin      → asigna RS activas a supervisores y usuarios
    Supervisor → asigna sus RS a sus usuarios
    """
    return razon_social_service.assign(
        body.user_id, body.razon_social_ids, db, current_user, request.client.host
    )


@router.delete("/assign/{user_id}/{razon_social_id}")
def unassign_razon_social(
    user_id: int,
    razon_social_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Quitar razón social de un usuario"""
    return razon_social_service.unassign(
        user_id, razon_social_id, db, current_user, request.client.host
    )
