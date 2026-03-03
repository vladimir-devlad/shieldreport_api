from sqlalchemy import Column, Integer, String, TIMESTAMP
from sqlalchemy.sql import func
from app.database import Base


class SyncLog(Base):
    __tablename__ = "sync_logs"

    id = Column(Integer, primary_key=True, index=True)
    table_name = Column(String(100), nullable=False)
    last_updated = Column(TIMESTAMP, nullable=False, server_default=func.now())
    operation = Column(String(10), nullable=False)
