from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.models import Meeting, Report
from app.schemas.schemas import (
    ScorecardResponse,
    MessageResponse
)
from app.services.analysis_service import AnalysisService
import logging

logger = logging.getLogger(__name__)
router = APIRouter(tags=["reports"])


@router.get("/{meeting_id}/scorecard", response_model=ScorecardResponse)
async def get_meeting_scorecard(
    meeting_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get meeting scorecard/analysis"""
    try:
        # Check if meeting exists
        result = await db.execute(select(Meeting).where(Meeting.id == meeting_id))
        meeting = result.scalar_one_or_none()
        
        if not meeting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Meeting not found"
            )
        
        # Check if meeting is completed
        if meeting.status != "COMPLETED":
            return ScorecardResponse(
                meeting_id=meeting_id,
                status="unavailable",
                message="Meeting is not completed yet"
            )
        
        # Get the latest report
        result = await db.execute(
            select(Report).where(Report.meeting_id == meeting_id).order_by(Report.created_at.desc())
        )
        report = result.scalar_one_or_none()
        
        if not report:
            return ScorecardResponse(
                meeting_id=meeting_id,
                status="processing",
                message="Analysis is in progress"
            )
        
        return ScorecardResponse(
            meeting_id=meeting_id,
            status="available",
            scorecard=report.score,
            created_at=report.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get scorecard for meeting {meeting_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get scorecard"
        )


@router.post("/{meeting_id}/trigger-analysis", response_model=MessageResponse)
async def trigger_analysis(
    meeting_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Manually trigger analysis for a meeting"""
    try:
        # Check if meeting exists
        result = await db.execute(select(Meeting).where(Meeting.id == meeting_id))
        meeting = result.scalar_one_or_none()
        
        if not meeting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Meeting not found"
            )
        
        # Check if meeting is completed
        if meeting.status != "COMPLETED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only analyze completed meetings"
            )
        
        # Trigger analysis
        analysis_service = AnalysisService()
        await analysis_service.trigger_analysis(meeting_id, db)
        
        return MessageResponse(message="Analysis triggered successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to trigger analysis for meeting {meeting_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to trigger analysis"
        ) 