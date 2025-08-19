import httpx
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.config import settings
from app.models.models import Meeting
from app.schemas.schemas import MeetingCreate, BotCreateResponse, StatusPollResponse
from app.models.enums import MeetingStatus

logger = logging.getLogger(__name__)


class BotService:
    def __init__(self):
        self.api_key = settings.attendee_api_key
        self.base_url = settings.attendee_api_base_url
        self.client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {self.api_key}",
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
                    "join_at": meeting.join_at.isoformat() if meeting.join_at else None
                }
            )
            
            db.add(db_meeting)
            await db.commit()
            await db.refresh(db_meeting)
            
            # Call Attendee API to create bot
            bot_data = await self._create_attendee_bot(meeting)
            
            # Update meeting with bot_id and status
            db_meeting.bot_id = bot_data["id"]
            db_meeting.status = MeetingStatus.STARTED
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
            if (status_data.get("transcription_state") == "complete" and 
                status_data.get("recording_state") == "complete"):
                return MeetingStatus.COMPLETED
            else:
                return MeetingStatus.FAILED
        elif attendee_state == "started":
            return MeetingStatus.STARTED
        elif attendee_state == "pending":
            return MeetingStatus.PENDING
        else:
            return MeetingStatus.FAILED
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose() 