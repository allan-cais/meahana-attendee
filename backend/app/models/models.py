from sqlalchemy import Column, Integer, String, DateTime, JSON, Enum, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
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
    
    # Relationships
    reports = relationship("Report", back_populates="meeting")
    transcript_chunks = relationship("TranscriptChunk", back_populates="meeting")


class WebhookEvent(Base):
    __tablename__ = "webhook_events"
    
    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, nullable=True)
    bot_id = Column(String, nullable=True)
    event_type = Column(String, nullable=False)
    event_data = Column(JSON, nullable=False)
    raw_payload = Column(JSON, nullable=False)
    processed = Column(String, default="false")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)


class TranscriptChunk(Base):
    __tablename__ = "transcript_chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"), nullable=False, index=True)
    speaker = Column(String, nullable=True)
    text = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    confidence = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=True)
    
    # Relationships
    meeting = relationship("Meeting", back_populates="transcript_chunks")


class Report(Base):
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"), nullable=False, index=True)
    score = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=True)
    
    # Relationships
    meeting = relationship("Meeting", back_populates="reports")
