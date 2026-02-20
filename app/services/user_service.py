from fastapi import HTTPException, status
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.role import Role
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _log(
    db: Session,
    user_id: int,
    action: str,
    table: str,
    record_id: int,
    old=None,
    new=None,
    ip=None,
):
    """Registra una acción en audit_logs"""
    log = AuditLog(
        user_id=user_id,
        action=action,
        table_name=table,
        record_id=record_id,
        old_data=old,
        new_data=new,
        ip_address=ip,
    )
    db.add(log)


def get_all_users(db: Session):
    return db.query(User).all()


def get_user_by_id(user_id: int, db: Session):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuario con id {user_id} no encontrado",
        )
    return user


def create_user(data: UserCreate, db: Session, current_user_id: int, ip: str = None):
    # verifica que el username no exista
    existing = db.query(User).filter(User.username == data.username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="El username ya está en uso"
        )

    # verifica que el rol exista
    role = db.query(Role).filter(Role.id == data.role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rol con id {data.role_id} no encontrado",
        )

    new_user = User(
        name=data.name,
        last_name=data.last_name,
        username=data.username,
        password=pwd_context.hash(data.password),
        role_id=data.role_id,
        is_active=True,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    _log(
        db,
        current_user_id,
        "CREATE_USER",
        "users",
        new_user.id,
        new={"username": new_user.username, "role_id": new_user.role_id},
        ip=ip,
    )
    db.commit()

    return new_user


def update_user(
    user_id: int, data: UserUpdate, db: Session, current_user_id: int, ip: str = None
):
    user = get_user_by_id(user_id, db)

    old_data = {
        "name": user.name,
        "last_name": user.last_name,
        "username": user.username,
        "role_id": user.role_id,
        "is_active": user.is_active,
    }

    # si cambia el username verifica que no exista
    if data.username and data.username != user.username:
        existing = db.query(User).filter(User.username == data.username).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El username ya está en uso",
            )

    # si cambia el rol verifica que exista
    if data.role_id:
        role = db.query(Role).filter(Role.id == data.role_id).first()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Rol con id {data.role_id} no encontrado",
            )

    # actualiza solo los campos enviados
    if data.name is not None:
        user.name = data.name
    if data.last_name is not None:
        user.last_name = data.last_name
    if data.username is not None:
        user.username = data.username
    if data.role_id is not None:
        user.role_id = data.role_id
    if data.is_active is not None:
        user.is_active = data.is_active
    if data.password is not None:
        user.password = pwd_context.hash(data.password)

    db.commit()
    db.refresh(user)

    new_data = {
        "name": user.name,
        "last_name": user.last_name,
        "username": user.username,
        "role_id": user.role_id,
        "is_active": user.is_active,
    }

    _log(
        db,
        current_user_id,
        "UPDATE_USER",
        "users",
        user.id,
        old=old_data,
        new=new_data,
        ip=ip,
    )
    db.commit()

    return user


def delete_user(user_id: int, db: Session, current_user_id: int, ip: str = None):
    user = get_user_by_id(user_id, db)

    # no puede eliminarse a sí mismo
    if user.id == current_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes desactivar tu propia cuenta",
        )

    # desactiva en lugar de eliminar
    user.is_active = False
    db.commit()

    _log(
        db,
        current_user_id,
        "DEACTIVATE_USER",
        "users",
        user.id,
        old={"is_active": True},
        new={"is_active": False},
        ip=ip,
    )
    db.commit()

    return {"message": f"Usuario {user.username} desactivado correctamente"}
