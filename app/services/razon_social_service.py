from typing import List

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.razon_social import RazonSocial
from app.models.user import User
from app.models.user_razon_social import UserRazonSocial
from app.models.user_supervisor import UserSupervisor
from app.schemas.razon_social import RazonSocialCreate, RazonSocialUpdate


def _log(db, user_id, action, record_id, old=None, new=None, ip=None):
    log = AuditLog(
        user_id=user_id,
        action=action,
        table_name="razon_social",
        record_id=record_id,
        old_data=old,
        new_data=new,
        ip_address=ip,
    )
    db.add(log)


def get_all(db: Session, current_user: User):
    """
    Superadmin → todas (activas e inactivas)
    Admin      → solo activas
    Supervisor → solo las suyas (activas)
    Usuario    → solo las suyas (activas)
    """
    if current_user.role.name == "superadmin":
        return db.query(RazonSocial).all()

    if current_user.role.name == "admin":
        return db.query(RazonSocial).filter(RazonSocial.is_active == True).all()

    # supervisor y usuario ven solo las suyas activas
    relations = (
        db.query(UserRazonSocial)
        .filter(UserRazonSocial.user_id == current_user.id)
        .all()
    )
    ids = [r.razon_social_id for r in relations]
    return (
        db.query(RazonSocial)
        .filter(RazonSocial.id.in_(ids), RazonSocial.is_active == True)
        .all()
    )


def get_by_id(razon_social_id: int, db: Session):
    rs = db.query(RazonSocial).filter(RazonSocial.id == razon_social_id).first()
    if not rs:
        raise HTTPException(status_code=404, detail="Razón social no encontrada")
    return rs


def create(data: RazonSocialCreate, db: Session, current_user_id: int, ip: str = None):
    existing = db.query(RazonSocial).filter(RazonSocial.name == data.name).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Ya existe una razón social con el nombre '{data.name}'",
        )
    rs = RazonSocial(name=data.name, is_active=False)  # inactiva por defecto
    db.add(rs)
    db.commit()
    db.refresh(rs)

    _log(
        db, current_user_id, "CREATE_RAZON_SOCIAL", rs.id, new={"name": rs.name}, ip=ip
    )
    db.commit()
    return rs


def update(
    razon_social_id: int,
    data: RazonSocialUpdate,
    db: Session,
    current_user_id: int,
    ip: str = None,
):
    rs = get_by_id(razon_social_id, db)
    old_data = {"name": rs.name, "is_active": rs.is_active}

    if data.name and data.name != rs.name:
        existing = db.query(RazonSocial).filter(RazonSocial.name == data.name).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Ya existe una razón social con el nombre '{data.name}'",
            )

    if data.name is not None:
        rs.name = data.name

    db.commit()
    db.refresh(rs)

    _log(
        db,
        current_user_id,
        "UPDATE_RAZON_SOCIAL",
        rs.id,
        old=old_data,
        new={"name": rs.name},
        ip=ip,
    )
    db.commit()
    return rs


def toggle_active(
    razon_social_id: int, db: Session, current_user_id: int, ip: str = None
):
    """Activa o desactiva una razón social — solo superadmin"""
    rs = get_by_id(razon_social_id, db)
    old_status = rs.is_active
    rs.is_active = not rs.is_active
    db.commit()
    db.refresh(rs)

    action = "ACTIVATE_RAZON_SOCIAL" if rs.is_active else "DEACTIVATE_RAZON_SOCIAL"
    _log(
        db,
        current_user_id,
        action,
        rs.id,
        old={"is_active": old_status},
        new={"is_active": rs.is_active},
        ip=ip,
    )
    db.commit()

    status_msg = "activada" if rs.is_active else "desactivada"
    return {
        "message": f"Razón social '{rs.name}' {status_msg} correctamente",
        "is_active": rs.is_active,
    }


def delete(razon_social_id: int, db: Session, current_user_id: int, ip: str = None):
    rs = get_by_id(razon_social_id, db)

    assigned = (
        db.query(UserRazonSocial)
        .filter(UserRazonSocial.razon_social_id == razon_social_id)
        .first()
    )
    if assigned:
        raise HTTPException(
            status_code=400,
            detail=f"No se puede eliminar '{rs.name}' porque tiene usuarios asignados",
        )

    _log(
        db, current_user_id, "DELETE_RAZON_SOCIAL", rs.id, old={"name": rs.name}, ip=ip
    )
    db.delete(rs)
    db.commit()
    return {"message": f"Razón social '{rs.name}' eliminada correctamente"}


def get_by_user(user_id: int, db: Session, current_user: User):
    if current_user.role.name == "supervisor":
        relation = (
            db.query(UserSupervisor)
            .filter(
                UserSupervisor.supervisor_id == current_user.id,
                UserSupervisor.user_id == user_id,
            )
            .first()
        )
        if not relation and user_id != current_user.id:
            raise HTTPException(
                status_code=403, detail="No tienes acceso a este usuario"
            )

    relations = (
        db.query(UserRazonSocial).filter(UserRazonSocial.user_id == user_id).all()
    )
    ids = [r.razon_social_id for r in relations]
    return (
        db.query(RazonSocial)
        .filter(RazonSocial.id.in_(ids), RazonSocial.is_active == True)
        .all()
    )


def assign(
    user_id: int,
    razon_social_ids: List[int],
    db: Session,
    current_user: User,
    ip: str = None,
):
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if current_user.role.name == "admin":
        # admin solo puede asignar RS activas
        for rs_id in razon_social_ids:
            rs = db.query(RazonSocial).filter(RazonSocial.id == rs_id).first()
            if not rs or not rs.is_active:
                raise HTTPException(
                    status_code=400,
                    detail=f"La razón social {rs_id} no existe o no está activa",
                )

    if current_user.role.name == "supervisor":
        relation = (
            db.query(UserSupervisor)
            .filter(
                UserSupervisor.supervisor_id == current_user.id,
                UserSupervisor.user_id == user_id,
            )
            .first()
        )
        if not relation:
            raise HTTPException(
                status_code=403,
                detail="No puedes asignar razones sociales a usuarios que no son tuyos",
            )

        my_relations = (
            db.query(UserRazonSocial)
            .filter(UserRazonSocial.user_id == current_user.id)
            .all()
        )
        my_ids = [r.razon_social_id for r in my_relations]
        for rs_id in razon_social_ids:
            if rs_id not in my_ids:
                raise HTTPException(
                    status_code=403,
                    detail=f"No puedes asignar la razón social {rs_id} porque no es tuya",
                )

    assigned = []
    for rs_id in razon_social_ids:
        existing = (
            db.query(UserRazonSocial)
            .filter(
                UserRazonSocial.user_id == user_id,
                UserRazonSocial.razon_social_id == rs_id,
            )
            .first()
        )
        if not existing:
            db.add(UserRazonSocial(user_id=user_id, razon_social_id=rs_id))
            assigned.append(rs_id)

    db.commit()

    _log(
        db,
        current_user.id,
        "ASSIGN_RAZON_SOCIAL",
        user_id,
        new={"user_id": user_id, "razon_social_ids": assigned},
        ip=ip,
    )
    db.commit()

    return {"message": "Razones sociales asignadas correctamente", "assigned": assigned}


def unassign(
    user_id: int, razon_social_id: int, db: Session, current_user: User, ip: str = None
):
    if current_user.role.name == "supervisor":
        relation = (
            db.query(UserSupervisor)
            .filter(
                UserSupervisor.supervisor_id == current_user.id,
                UserSupervisor.user_id == user_id,
            )
            .first()
        )
        if not relation:
            raise HTTPException(
                status_code=403,
                detail="No puedes modificar razones sociales de usuarios que no son tuyos",
            )

    assignment = (
        db.query(UserRazonSocial)
        .filter(
            UserRazonSocial.user_id == user_id,
            UserRazonSocial.razon_social_id == razon_social_id,
        )
        .first()
    )
    if not assignment:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")

    db.delete(assignment)
    db.commit()

    _log(
        db,
        current_user.id,
        "UNASSIGN_RAZON_SOCIAL",
        user_id,
        old={"user_id": user_id, "razon_social_id": razon_social_id},
        ip=ip,
    )
    db.commit()

    return {"message": "Razón social removida correctamente"}
