"""
src/models/meeting.py
----------------------
PostgreSQL-only Meeting entity model (SQLAlchemy 2.x async).

All MongoDB/Beanie dual-mode code has been removed.
"""

import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum
from sqlalchemy import Column, String, Integer, DateTime, JSON, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from src.models.base import Base


class MeetingStatus(str, PyEnum):
    """Pipeline lifecycle state for a Meeting record."""
    PENDING = "pending"
    PROCESSING = "processing"
    JOINING = "joining"
    RECORDING = "recording"
    TRANSCRIBING = "transcribing"
    SUMMARISING = "summarising"
    DELIVERING = "delivering"
    COMPLETED = "completed"
    FAILED = "failed"


class Meeting(Base):
    """SQLAlchemy model representing a meeting in PostgreSQL."""
    __tablename__ = "meetings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=True)
    meeting_link = Column(String(500), nullable=True)
    session_id = Column(String(100), nullable=True, index=True)
    platform = Column(String(50), nullable=True)
    scheduled_time = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    status = Column(
        SQLEnum(MeetingStatus),
        nullable=False,
        default=MeetingStatus.PROCESSING,
    )
    error_message = Column(Text, nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    transcript = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    action_items = Column(JSON, nullable=True, default=list)
    decisions = Column(JSON, nullable=True, default=list)
    follow_up = Column(JSON, nullable=True, default=list)
    speaker_stats = Column(JSON, nullable=True)

    # Tenant isolation
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
