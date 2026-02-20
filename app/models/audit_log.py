from sqlalchemy import TIMESTAMP, Column, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)
    table_name = Column(String(100), nullable=True)
    record_id = Column(Integer, nullable=True)
    old_data = Column(JSONB, nullable=True)
    new_data = Column(JSONB, nullable=True)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())

    user = relationship("User", back_populates="audit_logs")
