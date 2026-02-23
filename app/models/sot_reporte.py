from sqlalchemy import TIMESTAMP, BigInteger, Column, Integer, String, Text
from sqlalchemy.sql import func

from app.database import Base


class SotReporte(Base):
    __tablename__ = "sot_reportes"

    id = Column(BigInteger, primary_key=True, index=True)
    sot = Column(String(100))
    fecha_fecgensot = Column(String(100))
    hora_fecgensot = Column(String(100))
    proceso = Column(String(150))
    tipo_trabajo = Column(String(100))
    sub_tipo_orden = Column(String(100))
    estado_sot = Column(String(50))
    estado_agenda = Column(String(50))
    fecha_programada = Column(String(100))
    region = Column(String(100))
    departamento = Column(String(100))
    provincia = Column(String(100))
    distrito = Column(String(100))
    franja = Column(String(100))
    lugar_venta = Column(String(150))
    tipopuntoventa = Column(String(100))
    tipo_pdv = Column(String(100))
    pdv_region = Column(String(100))
    codusu = Column(String(50))
    cargo = Column(String(100))
    area = Column(String(100))
    direccion = Column(Text)
    confirmacion = Column(String(50))
    tipo_venta = Column(String(100))
    tipo_programacion = Column(String(100))
    dilacion = Column(String(100))
    usuario_venta = Column(String(100))
    ovenc_codigo = Column(String(100))
    fecha_carga = Column(String(100))
    pdv_razon_social = Column(String(255))
    razon_social_id = Column(Integer)
    created_at = Column(TIMESTAMP, server_default=func.now())
