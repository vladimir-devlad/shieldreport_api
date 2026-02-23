from fastapi import HTTPException
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.razon_social import RazonSocial
from app.models.role import Role
from app.models.user import User
from app.models.user_razon_social import UserRazonSocial
from app.models.user_supervisor import UserSupervisor
from app.schemas.user import UserCreate, UserUpdate

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _log(db, user_id, action, record_id, old=None, new=None, ip=None):
    log = AuditLog(
        user_id=user_id,
        action=action,
        table_name="users",
        record_id=record_id,
        old_data=old,
        new_data=new,
        ip_address=ip,
    )
    db.add(log)


def _build_user_detail(user: User, db: Session) -> dict:
    role_data = {"id": user.role.id, "name": user.role.name}

    # supervisor al que pertenece
    supervisor_data = None
    supervisor_relation = (
        db.query(UserSupervisor).filter(UserSupervisor.user_id == user.id).first()
    )
    if supervisor_relation:
        sup = (
            db.query(User).filter(User.id == supervisor_relation.supervisor_id).first()
        )
        if sup:
            supervisor_data = {
                "id": sup.id,
                "name": sup.name,
                "last_name": sup.last_name,
                "username": sup.username,
            }

    # usuarios que supervisa
    supervised = []
    if user.role.name == "supervisor":
        relations = (
            db.query(UserSupervisor)
            .filter(UserSupervisor.supervisor_id == user.id)
            .all()
        )
        for r in relations:
            u = db.query(User).filter(User.id == r.user_id).first()
            if u:
                # razones sociales del usuario supervisado
                rs_relations = (
                    db.query(UserRazonSocial)
                    .filter(UserRazonSocial.user_id == u.id)
                    .all()
                )
                rs_list = []
                for rsr in rs_relations:
                    rs = (
                        db.query(RazonSocial)
                        .filter(RazonSocial.id == rsr.razon_social_id)
                        .first()
                    )
                    if rs:
                        rs_list.append({"id": rs.id, "name": rs.name})

                supervised.append(
                    {
                        "id": u.id,
                        "name": u.name,
                        "last_name": u.last_name,
                        "username": u.username,
                        "is_active": u.is_active,
                        "razon_sociales": rs_list,
                    }
                )

    # razones sociales del usuario
    razon_relations = (
        db.query(UserRazonSocial).filter(UserRazonSocial.user_id == user.id).all()
    )
    razon_sociales = []
    for r in razon_relations:
        rs = db.query(RazonSocial).filter(RazonSocial.id == r.razon_social_id).first()
        if rs:
            razon_sociales.append({"id": rs.id, "name": rs.name})

    return {
        "id": user.id,
        "name": user.name,
        "last_name": user.last_name,
        "username": user.username,
        "is_active": user.is_active,
        "role_id": user.role_id,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
        "role": role_data,
        "supervisor": supervisor_data,
        "supervised_users": supervised,
        "razon_sociales": razon_sociales,
    }


def get_all_users(db: Session, current_user: User):
    if current_user.role.name == "superadmin":
        # superadmin ve absolutamente todos
        users = db.query(User).all()

    elif current_user.role.name == "admin":
        # admin ve todos EXCEPTO superadmins
        superadmin_role = db.query(Role).filter(Role.name == "superadmin").first()
        users = db.query(User).filter(User.role_id != superadmin_role.id).all()

    elif current_user.role.name == "supervisor":
        # supervisor ve solo su grupo
        relations = (
            db.query(UserSupervisor)
            .filter(UserSupervisor.supervisor_id == current_user.id)
            .all()
        )
        user_ids = [r.user_id for r in relations]
        users = db.query(User).filter(User.id.in_(user_ids)).all()

    else:
        return []

    return [_build_user_detail(u, db) for u in users]


def get_user_by_id(user_id: int, db: Session, current_user: User):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if current_user.role.name == "superadmin":
        # ve cualquier usuario
        return _build_user_detail(user, db)

    elif current_user.role.name == "admin":
        # admin no puede ver superadmins
        if user.role.name == "superadmin":
            raise HTTPException(
                status_code=403, detail="No tienes acceso a este usuario"
            )
        return _build_user_detail(user, db)

    elif current_user.role.name == "supervisor":
        # supervisor solo ve los suyos
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
                status_code=403, detail="No tienes acceso a este usuario"
            )
        return _build_user_detail(user, db)

    raise HTTPException(status_code=403, detail="No tienes acceso a este usuario")


def get_my_profile(db: Session, current_user: User):
    return _build_user_detail(current_user, db)


def get_users_sin_supervisor(db: Session):
    """
    Lista usuarios con rol 'usuario' que no tienen supervisor asignado.
    Disponible para admin y supervisor.
    """
    rol_usuario = db.query(Role).filter(Role.name == "usuario").first()
    if not rol_usuario:
        return []

    # todos los user_id que ya tienen supervisor
    asignados = db.query(UserSupervisor.user_id).all()
    asignados_ids = [r.user_id for r in asignados]

    # usuarios sin supervisor
    return (
        db.query(User)
        .filter(
            User.role_id == rol_usuario.id,
            User.is_active == True,
            ~User.id.in_(asignados_ids),
        )
        .all()
    )


def create_user(data: UserCreate, db: Session, current_user: User, ip: str = None):
    existing = db.query(User).filter(User.username == data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="El username ya está en uso")

    role = db.query(Role).filter(Role.id == data.role_id).first()
    if not role:
        raise HTTPException(
            status_code=404, detail=f"Rol con id {data.role_id} no encontrado"
        )

    # reglas de creación por rol
    if current_user.role.name == "superadmin":
        # superadmin puede crear cualquier rol
        pass

    elif current_user.role.name == "admin":
        # admin solo puede crear supervisor y usuario
        if role.name in ["superadmin", "admin"]:
            raise HTTPException(
                status_code=403,
                detail="El admin solo puede crear supervisores y usuarios",
            )

    else:
        raise HTTPException(
            status_code=403, detail="No tienes permisos para crear usuarios"
        )

    # si se envía supervisor_id validar que exista y sea supervisor
    if data.supervisor_id:
        supervisor = db.query(User).filter(User.id == data.supervisor_id).first()
        if not supervisor:
            raise HTTPException(status_code=404, detail="Supervisor no encontrado")
        if supervisor.role.name != "supervisor":
            raise HTTPException(
                status_code=400,
                detail=f"'{supervisor.username}' no tiene rol de supervisor",
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

    # vincula supervisor si se envió
    if data.supervisor_id:
        db.add(UserSupervisor(supervisor_id=data.supervisor_id, user_id=new_user.id))

    # asigna razones sociales si se enviaron
    # admin solo puede asignar RS activas
    for rs_id in data.razon_social_ids or []:
        rs = db.query(RazonSocial).filter(RazonSocial.id == rs_id).first()
        if not rs:
            raise HTTPException(
                status_code=404, detail=f"Razón social {rs_id} no encontrada"
            )
        if not rs.is_active:
            raise HTTPException(
                status_code=400, detail=f"La razón social '{rs.name}' no está activa"
            )
        db.add(UserRazonSocial(user_id=new_user.id, razon_social_id=rs_id))

    db.commit()

    _log(
        db,
        current_user.id,
        "CREATE_USER",
        new_user.id,
        new={
            "username": new_user.username,
            "role_id": new_user.role_id,
            "supervisor_id": data.supervisor_id,
            "razon_social_ids": data.razon_social_ids,
        },
        ip=ip,
    )
    db.commit()
    return _build_user_detail(new_user, db)


def update_user(
    user_id: int, data: UserUpdate, db: Session, current_user: User, ip: str = None
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # validación de cambio de contraseña por rol
    if data.password is not None:
        if current_user.role.name == "admin":
            # admin no puede cambiar contraseña de superadmin
            if user.role.name == "superadmin":
                raise HTTPException(
                    status_code=403,
                    detail="No puedes cambiar la contraseña de un superadmin",
                )

        elif current_user.role.name == "supervisor":
            # supervisor solo puede cambiar la de sus usuarios
            if user.role.name in ["superadmin", "admin"]:
                raise HTTPException(
                    status_code=403,
                    detail="No puedes cambiar la contraseña de un admin o superadmin",
                )
            # verifica que el usuario sea de su grupo
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
                    status_code=403,
                    detail="Solo puedes cambiar la contraseña de tus propios usuarios",
                )

    # resto de validaciones existentes...
    old_data = {
        "name": user.name,
        "last_name": user.last_name,
        "username": user.username,
        "role_id": user.role_id,
        "is_active": user.is_active,
    }

    if data.username and data.username != user.username:
        existing = db.query(User).filter(User.username == data.username).first()
        if existing:
            raise HTTPException(status_code=400, detail="El username ya está en uso")

    if data.role_id:
        role = db.query(Role).filter(Role.id == data.role_id).first()
        if not role:
            raise HTTPException(
                status_code=404, detail=f"Rol con id {data.role_id} no encontrado"
            )

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

    _log(db, current_user.id, "UPDATE_USER", user.id, old=old_data, new=new_data, ip=ip)
    db.commit()
    return _build_user_detail(user, db)


def deactivate_user(user_id: int, db: Session, current_user: User, ip: str = None):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if user.id == current_user.id:
        raise HTTPException(
            status_code=400, detail="No puedes desactivar tu propia cuenta"
        )

    user.is_active = False
    db.commit()

    _log(
        db,
        current_user.id,
        "DEACTIVATE_USER",
        user.id,
        old={"is_active": True},
        new={"is_active": False},
        ip=ip,
    )
    db.commit()
    return {"message": f"Usuario '{user.username}' desactivado correctamente"}


def change_my_password(new_password: str, db: Session, current_user: User):
    current_user.password = pwd_context.hash(new_password)
    db.commit()
    return {"message": "Contraseña actualizada correctamente"}
