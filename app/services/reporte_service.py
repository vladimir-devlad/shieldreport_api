import math
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.razon_social import RazonSocial
from app.models.sot_reporte import SotReporte
from app.models.user import User
from app.models.user_razon_social import UserRazonSocial


def _get_razon_social_ids(db: Session, current_user: User):
    """
    Superadmin → None (ve absolutamente todo sin filtro)
    Admin      → IDs de RS que tienen is_active = true
    Supervisor/Usuario → IDs de sus RS asignadas activas
    """
    if current_user.role.name == "superadmin":
        # sin restricción, ve todos los reportes
        return None

    if current_user.role.name == "admin":
        # ve reportes de todas las RS activas
        activas = db.query(RazonSocial).filter(RazonSocial.is_active == True).all()
        return [rs.id for rs in activas]

    # supervisor y usuario → solo sus RS asignadas activas
    relations = (
        db.query(UserRazonSocial)
        .filter(UserRazonSocial.user_id == current_user.id)
        .all()
    )
    rs_ids = [r.razon_social_id for r in relations]

    # filtra solo las que están activas
    activas = (
        db.query(RazonSocial)
        .filter(RazonSocial.id.in_(rs_ids), RazonSocial.is_active == True)
        .all()
    )
    return [rs.id for rs in activas]


def get_reportes(
    db: Session,
    current_user: User,
    razon_social_id: Optional[int] = None,
    page: int = 1,
    limit: int = 50,
):
    query = db.query(SotReporte)

    allowed_ids = _get_razon_social_ids(db, current_user)

    if allowed_ids is not None:
        if not allowed_ids:
            return {"total": 0, "page": page, "limit": limit, "pages": 0, "data": []}
        query = query.filter(SotReporte.razon_social_id.in_(allowed_ids))

    # filtro adicional por razon_social_id si se envía
    if razon_social_id:
        if allowed_ids is not None and razon_social_id not in allowed_ids:
            raise HTTPException(
                status_code=403, detail="No tienes acceso a esta razón social"
            )
        query = query.filter(SotReporte.razon_social_id == razon_social_id)

    total = query.count()
    pages = math.ceil(total / limit) if total > 0 else 0
    offset = (page - 1) * limit
    reportes = query.offset(offset).limit(limit).all()

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "pages": pages,
        "data": reportes,
    }


def get_reporte_by_id(reporte_id: int, db: Session, current_user: User):
    reporte = db.query(SotReporte).filter(SotReporte.id == reporte_id).first()
    if not reporte:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")

    allowed_ids = _get_razon_social_ids(db, current_user)
    if allowed_ids is not None:
        if reporte.razon_social_id not in allowed_ids:
            raise HTTPException(
                status_code=403, detail="No tienes acceso a este reporte"
            )

    return reporte
