from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.user import User
from app.models.user_supervisor import UserSupervisor


def _log(db, user_id, action, record_id, old=None, new=None, ip=None):
    log = AuditLog(
        user_id=user_id,
        action=action,
        table_name="user_supervisor",
        record_id=record_id,
        old_data=old,
        new_data=new,
        ip_address=ip,
    )
    db.add(log)


def agregar_usuario(
    supervisor_id: int, user_id: int, db: Session, current_user: User, ip: str = None
):
    """
    Supervisor jala un usuario sin supervisor a su grupo.
    Admin también puede hacer esto.
    """
    # verifica que el usuario exista
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # verifica que tenga rol usuario
    if user.role.name != "usuario":
        raise HTTPException(
            status_code=400, detail="Solo se pueden agregar usuarios con rol 'usuario'"
        )

    # verifica que no esté ya en este supervisor específico
    existing = (
        db.query(UserSupervisor)
        .filter(
            UserSupervisor.supervisor_id == supervisor_id,
            UserSupervisor.user_id == user_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"El usuario '{user.username}' ya está en este grupo",
        )

    # si es supervisor, solo puede agregarse usuarios a sí mismo
    if current_user.role.name == "supervisor":
        if supervisor_id != current_user.id:
            raise HTTPException(
                status_code=403, detail="Solo puedes agregar usuarios a tu propio grupo"
            )

    # verifica que el supervisor exista y tenga rol supervisor
    supervisor = db.query(User).filter(User.id == supervisor_id).first()
    if not supervisor or supervisor.role.name != "supervisor":
        raise HTTPException(status_code=404, detail="Supervisor no encontrado")

    relation = UserSupervisor(supervisor_id=supervisor_id, user_id=user_id)
    db.add(relation)
    db.commit()

    _log(
        db,
        current_user.id,
        "ADD_USER_TO_SUPERVISOR",
        user_id,
        new={"supervisor_id": supervisor_id, "user_id": user_id},
        ip=ip,
    )
    db.commit()

    return {"message": f"Usuario '{user.username}' agregado al grupo correctamente"}


def remover_usuario(
    supervisor_id: int, user_id: int, db: Session, current_user: User, ip: str = None
):
    """Remueve un usuario del grupo del supervisor"""

    if current_user.role.name == "supervisor" and supervisor_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Solo puedes remover usuarios de tu propio grupo"
        )

    relation = (
        db.query(UserSupervisor)
        .filter(
            UserSupervisor.supervisor_id == supervisor_id,
            UserSupervisor.user_id == user_id,
        )
        .first()
    )
    if not relation:
        raise HTTPException(
            status_code=404, detail="El usuario no pertenece a este supervisor"
        )

    user = db.query(User).filter(User.id == user_id).first()

    db.delete(relation)
    db.commit()

    _log(
        db,
        current_user.id,
        "REMOVE_USER_FROM_SUPERVISOR",
        user_id,
        old={"supervisor_id": supervisor_id, "user_id": user_id},
        ip=ip,
    )
    db.commit()

    return {"message": f"Usuario '{user.username}' removido del grupo correctamente"}
