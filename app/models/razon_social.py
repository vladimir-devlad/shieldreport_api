from sqlalchemy import TIMESTAMP, Boolean, Column, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class RazonSocial(Base):
    __tablename__ = "razon_social"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(300), nullable=False, unique=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now())

    usuarios = relationship("UserRazonSocial", back_populates="razon_social")
