from sqlalchemy import TIMESTAMP, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class UserSession(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token = Column(String(512), nullable=False, unique=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String, nullable=True)
    expires_at = Column(TIMESTAMP, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    user = relationship("User", back_populates="sessions")
