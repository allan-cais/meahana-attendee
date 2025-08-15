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


@router.delete("/{bot_id}")
async def delete_bot(bot_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a meeting bot"""
    try:
        result = await db.execute(select(Meeting).where(Meeting.id == bot_id))
        meeting = result.scalar_one_or_none()
        
        if not meeting:
            raise HTTPException(status_code=404, detail="Bot not found")
        
        # Delete the meeting (this will cascade to related records)
        await db.delete(meeting)
        await db.commit()
        
        logger.info(f"Deleted bot {bot_id}")
        return {"message": f"Bot {bot_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting bot {bot_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete bot")


@router.post("/{bot_id}/poll-status")
async def poll_bot_status(bot_id: int, db: AsyncSession = Depends(get_db)):
    """Manually poll the Attendee API for bot status updates"""
    try:
        result = await db.execute(select(Meeting).where(Meeting.id == bot_id))
        meeting = result.scalar_one_or_none()
        
        if not meeting:
            raise HTTPException(status_code=404, detail="Bot not found")
        
        if not meeting.bot_id:
            raise HTTPException(status_code=400, detail="Bot has no bot_id to poll")
        
        # Poll the Attendee API for status updates
        from app.services.bot_service import BotService
        status_data = await BotService.poll_bot_status(db, meeting.bot_id)
        
        # Extract status from the response and map to our enum values
        attendee_state = status_data.get("state", "unknown")
        logger.info(f"Bot {bot_id} state from Attendee API: {attendee_state}")
        
        # Map Attendee API state to our MeetingStatus enum
        if attendee_state == "ended":
            if status_data.get("transcription_state") == "complete" and status_data.get("recording_state") == "complete":
                bot_status = "COMPLETED"
            else:
                bot_status = "FAILED"
        elif attendee_state == "started":
            bot_status = "STARTED"
        elif attendee_state == "pending":
            bot_status = "PENDING"
        else:
            bot_status = "FAILED"
        
        logger.info(f"Mapped bot {bot_id} state '{attendee_state}' to status '{bot_status}'")
        
        # Update meeting status if it has changed
        if bot_status != meeting.status:
            logger.info(f"Updating meeting {bot_id} status from '{meeting.status}' to '{bot_status}'")
            await BotService.update_meeting_status(db, meeting, bot_status)
            
            # If bot is completed, trigger analysis
            if bot_status == "COMPLETED":
                logger.info(f"Bot {bot_id} completed, triggering analysis")
                from app.services.analysis_service import AnalysisService
                analysis_service = AnalysisService()
                await analysis_service.enqueue_analysis(db, meeting.id)
        
        return {
            "bot_id": bot_id,
            "old_status": meeting.status,
            "new_status": bot_status,
            "status_updated": bot_status != meeting.status,
            "attendee_api_data": status_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error polling bot status for {bot_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{bot_id}/add-webhook")
async def add_webhook_to_bot(bot_id: int, db: AsyncSession = Depends(get_db)):
    """Add webhook configuration to an existing bot"""
    try:
        result = await db.execute(select(Meeting).where(Meeting.id == bot_id))
        meeting = result.scalar_one_or_none()
        
        if not meeting:
            raise HTTPException(status_code=404, detail="Bot not found")
        
        if not meeting.bot_id:
            raise HTTPException(status_code=400, detail="Bot has no bot_id")
        
        # Add webhook to the bot via Attendee API
        from app.services.bot_service import BotService
        webhook_result = await BotService.add_webhook_to_existing_bot(db, meeting.bot_id)
        
        logger.info(f"Successfully added webhook to bot {bot_id}")
        
        return {
            "bot_id": bot_id,
            "message": "Webhook added successfully",
            "webhook_data": webhook_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding webhook to bot {bot_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


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

 