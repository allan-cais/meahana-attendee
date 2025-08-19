from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models.enums import MeetingStatus


# Base schemas
class MeetingBase(BaseModel):
    meeting_url: HttpUrl
    bot_id: Optional[str] = None
    join_at: Optional[datetime] = None


class MeetingCreate(MeetingBase):
    pass


class MeetingUpdate(BaseModel):
    meeting_url: Optional[HttpUrl] = None
    bot_name: Optional[str] = None
    join_at: Optional[datetime] = None


class MeetingResponse(MeetingBase):
    id: int
    bot_id: Optional[str] = None
    status: MeetingStatus
    meeting_metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Transcript schemas
class TranscriptChunkBase(BaseModel):
    speaker: Optional[str] = None
    text: str
    timestamp: datetime
    confidence: Optional[str] = None


class TranscriptChunkResponse(TranscriptChunkBase):
    id: int
    meeting_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Alias for backward compatibility
TranscriptChunkSchema = TranscriptChunkResponse


# Report schemas
class ReportScore(BaseModel):
    overall_score: float
    sentiment: str
    key_topics: List[str]
    action_items: List[str]
    participants: List[str]
    engagement_score: float
    meeting_effectiveness: float
    summary: str
    insights: List[str]
    recommendations: List[str]


class ReportResponse(BaseModel):
    id: int
    meeting_id: int
    score: ReportScore
    created_at: datetime

    class Config:
        from_attributes = True


# Alias for backward compatibility
ReportSchema = ReportResponse


# Webhook schemas
class WebhookPayload(BaseModel):
    data: Dict[str, Any]
    
    def get_event_type(self) -> str:
        """Extract event type from payload data"""
        return self.data.get("event_type", "unknown")
    
    def get_bot_id(self) -> Optional[str]:
        """Extract bot ID from payload data"""
        return self.data.get("bot_id")


# Composite schemas
class MeetingWithReport(BaseModel):
    meeting: MeetingResponse
    report: Optional[ReportResponse] = None

    class Config:
        from_attributes = True


class MeetingWithTranscripts(BaseModel):
    meeting: MeetingResponse
    transcript_chunks: List[TranscriptChunkResponse] = []

    class Config:
        from_attributes = True


class MeetingReportResponse(BaseModel):
    meeting_id: int
    status: str
    message: Optional[str] = None
    scorecard: Optional[ReportScore] = None
    created_at: Optional[datetime] = None


# Scorecard response
class ScorecardResponse(BaseModel):
    meeting_id: int
    status: str
    message: Optional[str] = None
    scorecard: Optional[ReportScore] = None
    created_at: Optional[datetime] = None


# Bot creation response
class BotCreateResponse(BaseModel):
    id: int
    meeting_url: str
    bot_id: str
    status: str
    meeting_metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


# Status polling response
class StatusPollResponse(BaseModel):
    status_updated: bool
    new_status: Optional[str] = None
    message: str


# API responses
class MessageResponse(BaseModel):
    message: str


class ListResponse(BaseModel):
    items: List[Any]
    total: int 