from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.role import Role
from app.models.user import User
from app.schemas.role import RoleCreate, RoleUpdate


def _log(
    db: Session, user_id: int, action: str, record_id: int, old=None, new=None, ip=None
):
    log = AuditLog(
        user_id=user_id,
        action=action,
        table_name="roles",
        record_id=record_id,
        old_data=old,
        new_data=new,
        ip_address=ip,
    )
    db.add(log)


def get_all_roles(db: Session):
    return db.query(Role).all()


def get_role_by_id(role_id: int, db: Session):
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rol con id {role_id} no encontrado",
        )
    return role


def create_role(data: RoleCreate, db: Session, current_user_id: int, ip: str = None):
    # verifica que no exista un rol con el mismo nombre
    existing = db.query(Role).filter(Role.name == data.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe un rol con el nombre '{data.name}'",
        )

    new_role = Role(name=data.name, description=data.description)
    db.add(new_role)
    db.commit()
    db.refresh(new_role)

    _log(
        db,
        current_user_id,
        "CREATE_ROLE",
        new_role.id,
        new={"name": new_role.name, "description": new_role.description},
        ip=ip,
    )
    db.commit()

    return new_role


def update_role(
    role_id: int, data: RoleUpdate, db: Session, current_user_id: int, ip: str = None
):
    role = get_role_by_id(role_id, db)

    old_data = {"name": role.name, "description": role.description}

    # verifica que el nuevo nombre no exista en otro rol
    if data.name and data.name != role.name:
        existing = db.query(Role).filter(Role.name == data.name).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe un rol con el nombre '{data.name}'",
            )

    if data.name is not None:
        role.name = data.name
    if data.description is not None:
        role.description = data.description

    db.commit()
    db.refresh(role)

    new_data = {"name": role.name, "description": role.description}

    _log(db, current_user_id, "UPDATE_ROLE", role.id, old=old_data, new=new_data, ip=ip)
    db.commit()

    return role


def delete_role(role_id: int, db: Session, current_user_id: int, ip: str = None):
    role = get_role_by_id(role_id, db)

    # verifica si hay usuarios con este rol
    users_with_role = db.query(User).filter(User.role_id == role_id).first()
    if users_with_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se puede eliminar el rol '{role.name}' porque tiene usuarios asignados",
        )

    _log(
        db,
        current_user_id,
        "DELETE_ROLE",
        role.id,
        old={"name": role.name, "description": role.description},
        ip=ip,
    )

    db.delete(role)
    db.commit()

    return {"message": f"Rol '{role.name}' eliminado correctamente"}
