"""
src/models/meeting.py
----------------------
Database document/table models for processed meetings.

Supports both Beanie ODM (MongoDB) and SQLAlchemy (PostgreSQL) based on the
DATABASE_TYPE environment variable.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Any, List, Dict

from pydantic import Field, BaseModel
from pydantic._internal._model_construction import ModelMetaclass

# ── Metaclass and Base Class Resolution ─────────────────────────────────────
DATABASE_TYPE = os.getenv("DATABASE_TYPE", "postgres").lower()

if DATABASE_TYPE == "mongodb":
    from beanie import Document
    BaseMeeting = Document
else:
    class PostgresModelMetaclass(ModelMetaclass):
        """Metaclass to allow Beanie-like syntax (e.g. Meeting.status == value) for SQL querying."""
        def __getattr__(cls, name):
            # Prevent recursion on pydantic internal fields
            if name.startswith('__') or name.startswith('_pydantic'):
                try:
                    return super().__getattr__(name)
                except AttributeError:
                    raise AttributeError(name)
            fields = cls.__dict__.get('__pydantic_fields__', {})
            if name in fields:
                class QueryFieldComparator:
                    def __init__(self, n):
                        self.n = n
                    def __eq__(self, other):
                        return {self.n: other}
                return QueryFieldComparator(name)
            try:
                return super().__getattr__(name)
            except AttributeError:
                raise AttributeError(name)

    class MeetingPostgresBase(BaseModel, metaclass=PostgresModelMetaclass):
        pass

    BaseMeeting = MeetingPostgresBase


# ── SQLAlchemy Declarative Base & Model ────────────────────────────────────
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, String, Integer, DateTime, JSON

Base = declarative_base()

class SQLMeeting(Base):
    """SQLAlchemy model representing a meeting in PostgreSQL."""
    __tablename__ = "meetings"

    id = Column(String, primary_key=True)
    title = Column(String, nullable=True)
    meeting_link = Column(String, nullable=True)
    session_id = Column(String, nullable=True)
    platform = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False)
    status = Column(String, nullable=False)
    error_message = Column(String, nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    transcript = Column(String, nullable=True)
    summary = Column(String, nullable=True)
    action_items = Column(JSON, nullable=True)  # JSON list of dicts
    decisions = Column(JSON, nullable=True)     # JSON list of strings
    follow_up = Column(JSON, nullable=True)     # JSON list of strings
    speaker_stats = Column(JSON, nullable=True)  # JSON dict


# ── Helper Query Wrapper ───────────────────────────────────────────────────
class PostgresQueryResult:
    """Helper to wrap query results and mimic Beanie's query runner."""
    def __init__(self, model_cls, filters: dict):
        self.model_cls = model_cls
        self.filters = filters

    async def to_list(self) -> list[Meeting]:
        from src.helpers.db import SessionLocal
        if SessionLocal is None:
            raise RuntimeError("PostgreSQL SessionLocal is not initialized.")
            
        async with SessionLocal() as session:
            from sqlalchemy import select
            stmt = select(SQLMeeting)
            for field, val in self.filters.items():
                col = getattr(SQLMeeting, field, None)
                if col is not None:
                    # Handle enum values
                    db_val = val.value if hasattr(val, "value") else val
                    stmt = stmt.where(col == db_val)
            # Order meetings newest-first
            stmt = stmt.order_by(SQLMeeting.created_at.desc())
            result = await session.execute(stmt)
            sql_meetings = result.scalars().all()
            return [self.model_cls.from_sql(m) for m in sql_meetings]


def parse_beanie_query(args) -> dict:
    """Converts Beanie comparison arguments (or dicts) into standard filter dicts."""
    filters = {}
    for arg in args:
        if isinstance(arg, dict):
            filters.update(arg)
        elif hasattr(arg, "items"):
            filters.update(dict(arg))
        elif hasattr(arg, "__iter__"):
            try:
                filters.update(dict(arg))
            except Exception:
                pass
    return filters


# ── Models & Sub-documents ──────────────────────────────────────────────────

class MeetingStatus(str, Enum):
    """Pipeline lifecycle state for a Meeting document."""
    PENDING = "pending"
    PROCESSING = "processing"
    JOINING = "joining"
    RECORDING = "recording"
    TRANSCRIBING = "transcribing"
    SUMMARISING = "summarising"
    DELIVERING = "delivering"
    COMPLETED = "completed"
    FAILED = "failed"


class ActionItem(BaseModel):
    """An accountable task extracted from the meeting transcript."""
    model_config = {"populate_by_name": True}
    assignee: str = Field(..., description="Person responsible for completing the task.")
    task: str = Field(..., description="Description of the task.")
    deadline: Optional[str] = Field(None, description="Target completion date or None.")


class SpeakerStats(BaseModel):
    """Speaker participation analytics embedded inside a Meeting document."""
    model_config = {"populate_by_name": True}
    speakers: list[dict] = Field(default_factory=list)
    most_active_speaker: Optional[str] = None
    total_meeting_duration_sec: float = 0.0
    detection_method: Optional[str] = None


class Meeting(BaseMeeting):
    """Canonical meeting document/table model."""
    
    # Declare primary key for PostgreSQL
    if DATABASE_TYPE != "mongodb":
        id: Optional[str] = Field(default=None, description="Database primary key.")

    # ── Identity / Metadata ──────────────────────────────────────────────
    title: Optional[str] = Field(None, description="Human-readable meeting title.")
    meeting_link: Optional[str] = Field(
        None, description="Original meeting URL used to launch the pipeline."
    )
    session_id: Optional[str] = Field(
        None, description="Optional custom session identifier for tracking."
    )
    platform: Optional[str] = Field(
        None, description="Source platform (e.g. 'Zoom', 'Google Meet')."
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp when the document was first created.",
    )

    # ── Pipeline lifecycle ───────────────────────────────────────────────
    status: MeetingStatus = Field(
        default=MeetingStatus.PROCESSING,
        description="Current pipeline lifecycle state.",
    )
    error_message: Optional[str] = Field(
        None, description="Human-readable error message if the meeting failed."
    )
    duration_minutes: Optional[int] = Field(
        None, description="Calculated meeting duration in whole minutes."
    )

    # ── Transcript ───────────────────────────────────────────────────────
    transcript: Optional[str] = Field(
        None,
        description="Full meeting transcript text (full_text from TranscriptResult).",
    )

    # ── Summarisation outputs ────────────────────────────────────────────
    summary: Optional[str] = Field(
        None, description="Markdown-formatted meeting summary from the LLM."
    )
    action_items: list[dict] = Field(
        default_factory=list,
        description="List of ActionItem dicts extracted by the LLM.",
    )
    decisions: list[str] = Field(
        default_factory=list,
        description="Key decisions reached during the meeting.",
    )
    follow_up: list[str] = Field(
        default_factory=list,
        description="Follow-up points to be addressed after the meeting.",
    )

    # ── Speaker analytics ────────────────────────────────────────────────
    speaker_stats: Optional[dict] = Field(
        None,
        description="Participation analytics (SpeakerStats dict or None if unavailable).",
    )

    class Settings:
        name = "meetings"

    # ── PostgreSQL Database Operations ──────────────────────────────────────

    @classmethod
    def from_sql(cls, sql_meeting: SQLMeeting) -> Meeting:
        return cls(
            id=sql_meeting.id,
            title=sql_meeting.title,
            meeting_link=sql_meeting.meeting_link,
            session_id=sql_meeting.session_id,
            platform=sql_meeting.platform,
            created_at=sql_meeting.created_at or datetime.now(timezone.utc),
            status=MeetingStatus(sql_meeting.status) if sql_meeting.status else MeetingStatus.PROCESSING,
            error_message=sql_meeting.error_message,
            duration_minutes=sql_meeting.duration_minutes,
            transcript=sql_meeting.transcript,
            summary=sql_meeting.summary,
            action_items=sql_meeting.action_items or [],
            decisions=sql_meeting.decisions or [],
            follow_up=sql_meeting.follow_up or [],
            speaker_stats=sql_meeting.speaker_stats,
        )

    def to_sql(self) -> SQLMeeting:
        db_status = self.status.value if hasattr(self.status, "value") else self.status
        return SQLMeeting(
            id=self.id,
            title=self.title,
            meeting_link=self.meeting_link,
            session_id=self.session_id,
            platform=self.platform,
            created_at=self.created_at,
            status=db_status,
            error_message=self.error_message,
            duration_minutes=self.duration_minutes,
            transcript=self.transcript,
            summary=self.summary,
            action_items=self.action_items,
            decisions=self.decisions,
            follow_up=self.follow_up,
            speaker_stats=self.speaker_stats,
        )

    async def insert(self) -> Meeting:
        if DATABASE_TYPE == "mongodb":
            return await super().insert()
            
        import uuid
        if not self.id:
            self.id = str(uuid.uuid4())
            
        from src.helpers.db import SessionLocal
        if SessionLocal is None:
            raise RuntimeError("PostgreSQL SessionLocal is not initialized.")
            
        async with SessionLocal() as session:
            sql_meeting = self.to_sql()
            session.add(sql_meeting)
            await session.commit()
        return self

    async def save(self) -> Meeting:
        if DATABASE_TYPE == "mongodb":
            return await super().save()
            
        from src.helpers.db import SessionLocal
        if SessionLocal is None:
            raise RuntimeError("PostgreSQL SessionLocal is not initialized.")
            
        async with SessionLocal() as session:
            from sqlalchemy import select
            stmt = select(SQLMeeting).where(SQLMeeting.id == self.id)
            result = await session.execute(stmt)
            sql_meeting = result.scalar_one_or_none()
            
            db_status = self.status.value if hasattr(self.status, "value") else self.status
            if sql_meeting:
                sql_meeting.title = self.title
                sql_meeting.meeting_link = self.meeting_link
                sql_meeting.session_id = self.session_id
                sql_meeting.platform = self.platform
                sql_meeting.created_at = self.created_at
                sql_meeting.status = db_status
                sql_meeting.error_message = self.error_message
                sql_meeting.duration_minutes = self.duration_minutes
                sql_meeting.transcript = self.transcript
                sql_meeting.summary = self.summary
                sql_meeting.action_items = self.action_items
                sql_meeting.decisions = self.decisions
                sql_meeting.follow_up = self.follow_up
                sql_meeting.speaker_stats = self.speaker_stats
            else:
                sql_meeting = self.to_sql()
                session.add(sql_meeting)
            await session.commit()
        return self

    @classmethod
    async def get(cls, id: Any) -> Optional[Meeting]:
        if DATABASE_TYPE == "mongodb":
            from beanie import PydanticObjectId
            try:
                oid = PydanticObjectId(id) if not isinstance(id, PydanticObjectId) else id
                return await super().get(oid)
            except Exception:
                return await super().get(id)
                
        from src.helpers.db import SessionLocal
        if SessionLocal is None:
            raise RuntimeError("PostgreSQL SessionLocal is not initialized.")
            
        str_id = str(id)
        async with SessionLocal() as session:
            from sqlalchemy import select
            stmt = select(SQLMeeting).where(SQLMeeting.id == str_id)
            result = await session.execute(stmt)
            sql_meeting = result.scalar_one_or_none()
            if sql_meeting:
                return cls.from_sql(sql_meeting)
        return None

    @classmethod
    async def find_one(cls, *args, **kwargs) -> Optional[Meeting]:
        if DATABASE_TYPE == "mongodb":
            return await super().find_one(*args, **kwargs)
            
        from src.helpers.db import SessionLocal
        if SessionLocal is None:
            raise RuntimeError("PostgreSQL SessionLocal is not initialized.")
            
        filters = parse_beanie_query(args)
        async with SessionLocal() as session:
            from sqlalchemy import select
            stmt = select(SQLMeeting)
            for field, val in filters.items():
                col = getattr(SQLMeeting, field, None)
                if col is not None:
                    db_val = val.value if hasattr(val, "value") else val
                    stmt = stmt.where(col == db_val)
            result = await session.execute(stmt)
            sql_meeting = result.scalar_one_or_none()
            if sql_meeting:
                return cls.from_sql(sql_meeting)
        return None

    @classmethod
    def find_all(cls) -> PostgresQueryResult:
        if DATABASE_TYPE == "mongodb":
            return super().find_all()
            
        return PostgresQueryResult(cls, filters={})

    @classmethod
    def find(cls, *args) -> PostgresQueryResult:
        if DATABASE_TYPE == "mongodb":
            return super().find(*args)
            
        filters = parse_beanie_query(args)
        return PostgresQueryResult(cls, filters=filters)
