from sqlalchemy import TIMESTAMP, Column, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class UserSupervisor(Base):
    __tablename__ = "user_supervisor"

    supervisor_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    created_at = Column(TIMESTAMP, server_default=func.now())

    supervisor = relationship(
        "User", foreign_keys=[supervisor_id], back_populates="supervised_users"
    )
    user = relationship("User", foreign_keys=[user_id], back_populates="supervisors")
