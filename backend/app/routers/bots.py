from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.config import settings
from app.schemas.schemas import MeetingCreate, MeetingResponse
from app.services.bot_service import BotService
from app.models.models import Meeting
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/bots", tags=["bots"])


@router.get("/", response_model=list[MeetingResponse])
async def get_bots(db: AsyncSession = Depends(get_db)):
    """Get all meeting bots"""
    try:
        result = await db.execute(select(Meeting).order_by(Meeting.created_at.desc()))
        meetings = result.scalars().all()
        return [MeetingResponse.model_validate(meeting) for meeting in meetings]
    except Exception as e:
        logger.error(f"Error getting bots: {e}")
        raise HTTPException(status_code=500, detail="Failed to get bots")


@router.get("/{bot_id}", response_model=MeetingResponse)
async def get_bot(bot_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific meeting bot by ID"""
    try:
        result = await db.execute(select(Meeting).where(Meeting.id == bot_id))
        meeting = result.scalar_one_or_none()
        
        if not meeting:
            raise HTTPException(status_code=404, detail="Bot not found")
            
        return MeetingResponse.model_validate(meeting)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting bot {bot_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get bot")


@router.post("/", response_model=MeetingResponse)
async def create_bot(
    meeting_data: MeetingCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new meeting bot and wait for bot_id from Attendee API"""
    try:
        # First insert the meeting in pending status
        meeting = await BotService.insert_pending_meeting(db, meeting_data)
        
        # Call Attendee API and wait for bot_id
        bot_id = await BotService.call_attendee_api(
            meeting_data.meeting_url,
            meeting_data.bot_name,
            meeting_data.join_at
        )
        
        # Update meeting with bot_id and status
        meeting = await BotService.update_meeting_with_bot_id(db, meeting, bot_id)
        
        # Debug logging to see what we're getting
        logger.info(f"Meeting object after update: {meeting}")
        logger.info(f"Meeting type: {type(meeting)}")
        logger.info(f"Meeting id: {meeting.id}")
        logger.info(f"Meeting created_at: {meeting.created_at}")
        logger.info(f"Meeting updated_at: {meeting.updated_at}")
        
        # Use the Pydantic model's from_attributes feature
        return MeetingResponse.model_validate(meeting)
        
    except Exception as e:
        logger.error(f"Error creating bot: {e}")
        logger.error(f"Error type: {type(e)}")
        logger.error(f"Error details: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Failed to create bot")

 