from sqlalchemy import TIMESTAMP, Column, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class UserRazonSocial(Base):
    __tablename__ = "user_razon_social"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    razon_social_id = Column(Integer, ForeignKey("razon_social.id"), primary_key=True)
    created_at = Column(TIMESTAMP, server_default=func.now())

    user = relationship("User", back_populates="razon_sociales")
    razon_social = relationship("RazonSocial", back_populates="usuarios")
