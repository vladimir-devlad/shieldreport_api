from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.reporte import ReportePaginado, ReporteResponse
from app.services import reporte_service

router = APIRouter(prefix="/reportes", tags=["Reportes SOT"])


@router.get("/", response_model=ReportePaginado)
def list_reportes(
    razon_social_id: Optional[int] = Query(
        None, description="Filtrar por razón social"
    ),
    page: int = Query(1, ge=1, description="Número de página"),
    limit: int = Query(50, ge=1, le=500, description="Registros por página"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Lista reportes SOT filtrados por rol y razón social.
    Admin ve todo, supervisor y usuario solo sus razones sociales.
    """
    return reporte_service.get_reportes(db, current_user, razon_social_id, page, limit)


@router.get("/{reporte_id}", response_model=ReporteResponse)
def get_reporte(
    reporte_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Detalle de un reporte — acceso filtrado por rol"""
    return reporte_service.get_reporte_by_id(reporte_id, db, current_user)
