from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ReporteResponse(BaseModel):
    id: int
    sot: Optional[str]
    fecha_fecgensot: Optional[str]
    hora_fecgensot: Optional[str]
    proceso: Optional[str]
    tipo_trabajo: Optional[str]
    sub_tipo_orden: Optional[str]
    estado_sot: Optional[str]
    estado_agenda: Optional[str]
    fecha_programada: Optional[str]
    region: Optional[str]
    departamento: Optional[str]
    provincia: Optional[str]
    distrito: Optional[str]
    franja: Optional[str]
    lugar_venta: Optional[str]
    tipopuntoventa: Optional[str]
    tipo_pdv: Optional[str]
    pdv_region: Optional[str]
    codusu: Optional[str]
    cargo: Optional[str]
    area: Optional[str]
    direccion: Optional[str]
    confirmacion: Optional[str]
    tipo_venta: Optional[str]
    tipo_programacion: Optional[str]
    dilacion: Optional[str]
    usuario_venta: Optional[str]
    ovenc_codigo: Optional[str]
    fecha_carga: Optional[str]
    pdv_razon_social: Optional[str]
    razon_social_id: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class ReportePaginado(BaseModel):
    total: int
    page: int
    limit: int
    pages: int
    data: list[ReporteResponse]
