import httpx
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.config import settings
from app.models.models import Meeting
from app.schemas.schemas import MeetingCreate, BotCreateResponse, StatusPollResponse
from app.models.enums import MeetingStatus
from typing import Optional

logger = logging.getLogger(__name__)


class BotService:
    def __init__(self):
        self.api_key = settings.attendee_api_key
        self.base_url = settings.attendee_api_base_url
        self.client = httpx.AsyncClient(
            headers={
                "Authorization": f"Token {self.api_key}",
                "Content-Type": "application/json"
            },
            timeout=30.0
        )
    
    async def create_bot(self, meeting: MeetingCreate, db: AsyncSession) -> BotCreateResponse:
        """Create a new meeting bot"""
        try:
            # Create meeting record in pending status
            db_meeting = Meeting(
                meeting_url=str(meeting.meeting_url),
                status=MeetingStatus.PENDING,
                meeting_metadata={
                    "bot_name": meeting.bot_name,
                    "join_at": meeting.join_at.isoformat() if meeting.join_at else None,
                    "webhook_base_url": getattr(meeting, 'webhook_base_url', None)
                }
            )
            
            # Add to session but don't commit yet
            db.add(db_meeting)
            await db.flush()  # Get the ID without committing
            
            # Call Attendee API to create bot
            bot_data = await self._create_attendee_bot(meeting)
            
            # Update meeting with bot_id and status
            db_meeting.bot_id = bot_data["id"]
            db_meeting.status = MeetingStatus.STARTED
            
            # Now commit everything in a single transaction
            await db.commit()
            await db.refresh(db_meeting)
            
            return BotCreateResponse(
                id=db_meeting.id,
                meeting_url=db_meeting.meeting_url,
                bot_id=db_meeting.bot_id,
                status=db_meeting.status.value,
                meeting_metadata=db_meeting.meeting_metadata,
                created_at=db_meeting.created_at,
                updated_at=db_meeting.updated_at
            )
            
        except Exception as e:
            logger.error(f"Failed to create bot: {e}")
            await db.rollback()
            raise
    
    async def poll_bot_status(self, bot_id: int, db: AsyncSession) -> StatusPollResponse:
        """Poll for bot status updates"""
        try:
            # Get meeting
            result = await db.execute(select(Meeting).where(Meeting.id == bot_id))
            meeting = result.scalar_one_or_none()
            
            if not meeting or not meeting.bot_id:
                return StatusPollResponse(
                    status_updated=False,
                    message="Meeting or bot_id not found"
                )
            
            # Poll Attendee API
            status_data = await self._get_bot_status(meeting.bot_id)
            
            # Map status
            attendee_state = status_data.get("state", "unknown")
            new_status = self._map_attendee_status(attendee_state, status_data)
            
            # If new_status is None, no status change needed
            if new_status is None:
                return StatusPollResponse(
                    status_updated=False,
                    message=f"No status change needed for state: {attendee_state}"
                )
            
            # Check if status changed
            status_updated = new_status != meeting.status
            
            if status_updated:
                # Update meeting status
                meeting.status = new_status
                await db.commit()
                
                return StatusPollResponse(
                    status_updated=True,
                    new_status=new_status.value,
                    message=f"Status updated from {meeting.status} to {new_status.value}"
                )
            
            return StatusPollResponse(
                status_updated=False,
                message="No status change"
            )
            
        except Exception as e:
            logger.error(f"Failed to poll bot status: {e}")
            raise
    
    async def _create_attendee_bot(self, meeting: MeetingCreate) -> dict:
        """Create bot via Attendee API"""
        payload = {
            "meeting_url": str(meeting.meeting_url),
            "bot_name": meeting.bot_name
        }
        
        if meeting.join_at:
            payload["join_at"] = meeting.join_at.isoformat()
        
        # Add webhooks configuration - REQUIRED for bot-level webhooks to work
        webhook_url = f"{meeting.webhook_base_url.rstrip('/')}/webhook/"
        payload["webhooks"] = [
            {
                "url": webhook_url,
                "triggers": [
                    "bot.state_change",
                    "transcript.update",
                    "chat_messages.update", 
                    "participant_events.join_leave"
                ]
            }
        ]
        
        response = await self.client.post(
            f"{self.base_url}/api/v1/bots",
            json=payload
        )
        response.raise_for_status()
        
        return response.json()
    
    async def _get_bot_status(self, attendee_bot_id: str) -> dict:
        """Get bot status from Attendee API"""
        response = await self.client.get(
            f"{self.base_url}/api/v1/bots/{attendee_bot_id}"
        )
        response.raise_for_status()
        
        return response.json()
    
    def _map_attendee_status(self, attendee_state: str, status_data: dict) -> MeetingStatus:
        """Map Attendee API state to our MeetingStatus enum"""
        if attendee_state == "ended":
            # Only set FAILED if there's a genuine error
            if (status_data.get("transcription_state") == "complete" and 
                status_data.get("recording_state") == "complete"):
                return MeetingStatus.COMPLETED
            elif (status_data.get("transcription_state") == "error" or 
                  status_data.get("recording_state") == "error"):
                return MeetingStatus.FAILED
            else:
                # Meeting ended but processing might still be ongoing
                return MeetingStatus.COMPLETED
        elif attendee_state == "started":
            return MeetingStatus.STARTED
        elif attendee_state == "pending":
            return MeetingStatus.PENDING
        elif attendee_state == "joining":
            return MeetingStatus.STARTED
        elif attendee_state == "recording":
            return MeetingStatus.STARTED
        elif attendee_state == "transcribing":
            return MeetingStatus.STARTED
        else:
            # Don't default to FAILED for unknown states - keep current status
            return None  # Return None to indicate no status change
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    @staticmethod
    async def update_meeting_status(db: AsyncSession, meeting: Meeting, status: str, commit: bool = True):
        """Update meeting status"""
        from app.models.enums import MeetingStatus
        
        try:
            # Convert string status to enum if needed
            if isinstance(status, str):
                status = MeetingStatus(status.upper())
            
            meeting.status = status
            
            # Only commit if explicitly requested (not from webhook context)
            if commit:
                await db.commit()
            
        except Exception as e:
            logger.error(f"Failed to update meeting {meeting.id} status to {status}: {e}")
            if commit:
                await db.rollback()
            raise
    
    @staticmethod
    async def get_meeting_by_bot_id(db: AsyncSession, bot_id: str) -> Optional[Meeting]:
        """Get meeting by bot_id"""
        from sqlalchemy import select
        
        result = await db.execute(
            select(Meeting).where(Meeting.bot_id == bot_id)
        )
        return result.scalar_one_or_none() 