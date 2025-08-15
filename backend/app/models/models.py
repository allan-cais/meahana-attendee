from sqlalchemy import Column, Integer, String, DateTime, JSON, Enum, Text
from sqlalchemy.sql import func
from app.core.database import Base
from app.models.enums import MeetingStatus


class Meeting(Base):
    __tablename__ = "meetings"
    
    id = Column(Integer, primary_key=True, index=True)
    meeting_url = Column(String, nullable=False, index=True)
    bot_id = Column(String, nullable=True, index=True)
    status = Column(Enum(MeetingStatus), nullable=False)
    meeting_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)


class WebhookEvent(Base):
    __tablename__ = "webhook_events"
    
    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, nullable=True)
    event_type = Column(String, nullable=False)
    payload = Column(JSON, nullable=False)
    processed = Column(String, default="false")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=True)


class TranscriptChunk(Base):
    __tablename__ = "transcript_chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, nullable=False)
    speaker = Column(String, nullable=True)
    text = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    confidence = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=True)


class Report(Base):
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True, index=True)
    score = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=True)
