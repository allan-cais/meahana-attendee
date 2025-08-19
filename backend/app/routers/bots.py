from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.core.database import get_db
from app.models.models import Meeting
from app.schemas.schemas import (
    MeetingCreate, 
    MeetingResponse, 
    BotCreateResponse,
    StatusPollResponse,
    MessageResponse,
    ListResponse
)
from app.services.bot_service import BotService
import logging

logger = logging.getLogger(__name__)
router = APIRouter(tags=["bots"])


@router.post("/bots/", response_model=BotCreateResponse)
async def create_bot(
    meeting: MeetingCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new meeting bot"""
    try:
        bot_service = BotService()
        result = await bot_service.create_bot(meeting, db)
        return result
    except Exception as e:
        logger.error(f"Failed to create bot: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create bot"
        )


@router.get("/bots/", response_model=ListResponse)
async def get_bots(db: AsyncSession = Depends(get_db)):
    """Get all bots"""
    try:
        result = await db.execute(select(Meeting).order_by(Meeting.created_at.desc()))
        meetings = result.scalars().all()
        
        return ListResponse(
            items=[MeetingResponse.model_validate(meeting) for meeting in meetings],
            total=len(meetings)
        )
    except Exception as e:
        logger.error(f"Failed to get bots: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get bots"
        )


@router.get("/bots/{bot_id}", response_model=MeetingResponse)
async def get_bot(bot_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific bot by ID"""
    try:
        result = await db.execute(select(Meeting).where(Meeting.id == bot_id))
        meeting = result.scalar_one_or_none()
        
        if not meeting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bot not found"
            )
        
        return MeetingResponse.model_validate(meeting)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get bot {bot_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get bot"
        )


@router.delete("/bots/{bot_id}", response_model=MessageResponse)
async def delete_bot(bot_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a bot"""
    try:
        result = await db.execute(select(Meeting).where(Meeting.id == bot_id))
        meeting = result.scalar_one_or_none()
        
        if not meeting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bot not found"
            )
        
        await db.execute(delete(Meeting).where(Meeting.id == bot_id))
        await db.commit()
        
        return MessageResponse(message="Bot deleted successfully")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete bot {bot_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete bot"
        )


@router.post("/bots/{bot_id}/poll-status", response_model=StatusPollResponse)
async def poll_bot_status(
    bot_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Poll for bot status updates"""
    try:
        bot_service = BotService()
        result = await bot_service.poll_bot_status(bot_id, db)
        return result
    except Exception as e:
        logger.error(f"Failed to poll bot status for {bot_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to poll bot status"
        )

 