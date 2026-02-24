from sqlalchemy import TIMESTAMP, Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    middle_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=False)
    second_last_name = Column(String(100), nullable=True)
    username = Column(String(50), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now())

    # relaciones
    role = relationship("Role", back_populates="users")
    sessions = relationship("UserSession", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")

    # relaciones nuevas
    emails = relationship("UserEmail", back_populates="user", cascade="all, delete")
    phones = relationship("UserPhone", back_populates="user", cascade="all, delete")

    supervised_users = relationship(
        "UserSupervisor",
        foreign_keys="UserSupervisor.supervisor_id",
        back_populates="supervisor",
    )
    supervisors = relationship(
        "UserSupervisor", foreign_keys="UserSupervisor.user_id", back_populates="user"
    )

    # razones sociales asignadas
    razon_sociales = relationship("UserRazonSocial", back_populates="user")
