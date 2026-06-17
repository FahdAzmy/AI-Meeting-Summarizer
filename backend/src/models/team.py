# src/models/team.py
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from src.models.base import Base


class Team(Base):
    __tablename__ = "teams"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    leader_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    company_id = Column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False
    )
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
