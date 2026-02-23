from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_admin_or_supervisor
from app.models.user import User
from app.schemas.supervisor import AgregarUsuarioRequest, RemoverUsuarioRequest
from app.services import supervisor_service

router = APIRouter(prefix="/supervisor", tags=["Supervisor"])


@router.post("/agregar-usuario")
def agregar_usuario(
    request: Request,
    body: AgregarUsuarioRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_supervisor),
):
    """
    Agrega un usuario sin supervisor al grupo.
    Admin puede asignar a cualquier supervisor.
    Supervisor solo puede agregar a su propio grupo.
    """
    return supervisor_service.agregar_usuario(
        body.supervisor_id, body.user_id, db, current_user, request.client.host
    )


@router.delete("/remover-usuario")
def remover_usuario(
    request: Request,
    body: RemoverUsuarioRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_supervisor),
):
    """
    Remueve un usuario del grupo del supervisor.
    Admin puede remover de cualquier grupo.
    Supervisor solo puede remover de su propio grupo.
    """
    return supervisor_service.remover_usuario(
        body.supervisor_id, body.user_id, db, current_user, request.client.host
    )
