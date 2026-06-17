# src/models/user.py
import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from src.models.base import Base


class UserRole(str, PyEnum):
    HR = "hr"
    TEAM_LEADER = "team_leader"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False)
    company_id = Column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False
    )
    is_active = Column(Boolean, default=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
