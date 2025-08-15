from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.core.config import settings
from app.models.models import Meeting
from app.schemas.schemas import MeetingWithReport, MeetingWithTranscripts, MeetingReportResponse
from app.services.analysis_service import AnalysisService
from app.services.transcript_service import TranscriptService
from app.models.enums import MeetingStatus
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/meeting", tags=["reports"])


@router.post("/{meeting_id}/trigger-analysis")
async def trigger_meeting_analysis(
    meeting_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Manually trigger analysis for a meeting"""
    try:
        # Get meeting
        result = await db.execute(
            select(Meeting).where(Meeting.id == meeting_id)
        )
        meeting = result.scalar_one_or_none()
        
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
        
        if meeting.status != MeetingStatus.COMPLETED:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot analyze meeting with status '{meeting.status}'. Meeting must be completed."
            )
        
        # Trigger analysis
        analysis_service = AnalysisService()
        await analysis_service.enqueue_analysis(db, meeting_id)
        
        return {"message": f"Analysis triggered for meeting {meeting_id}"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering analysis for meeting {meeting_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{meeting_id}/fetch-transcript")
async def fetch_meeting_transcript(
    meeting_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Manually fetch transcript from Attendee API for a meeting"""
    logger.info(f"🚀 Starting transcript fetch for meeting {meeting_id}")
    
    try:
        # Get meeting
        result = await db.execute(
            select(Meeting).where(Meeting.id == meeting_id)
        )
        meeting = result.scalar_one_or_none()
        
        if not meeting:
            logger.error(f"❌ Meeting not found for meeting_id: {meeting_id}")
            raise HTTPException(status_code=404, detail="Meeting not found")
        
        if not meeting.bot_id:
            logger.error(f"❌ Meeting {meeting_id} has no bot_id associated")
            raise HTTPException(
                status_code=400, 
                detail="Meeting has no bot_id associated"
            )
        
        logger.info(f"✅ Found meeting {meeting_id} with bot_id: {meeting.bot_id}")
        
        # Fetch transcript from Attendee API
        logger.info(f"📥 Fetching transcript from Attendee API for bot {meeting.bot_id}")
        transcript_service = TranscriptService()
        transcript_chunks = await transcript_service.fetch_full_transcript(db, meeting.bot_id)
        
        logger.info(f"✅ Successfully fetched {len(transcript_chunks)} transcript chunks")
        
        return {
            "message": f"Transcript fetched successfully for meeting {meeting_id}",
            "transcript_chunks_count": len(transcript_chunks),
            "bot_id": meeting.bot_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching transcript for meeting {meeting_id}: {e}")
        import traceback
        logger.error(f"📚 Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/{meeting_id}/report", response_model=MeetingReportResponse)
async def get_meeting_report(
    meeting_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get meeting report with analysis (reports only)"""
    try:
        # Get meeting with reports only
        result = await db.execute(
            select(Meeting)
            .options(selectinload(Meeting.reports))
            .where(Meeting.id == meeting_id)
        )
        meeting = result.scalar_one_or_none()
        
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
        
        # Determine message based on meeting status and reports
        message = None
        if not meeting.reports:
            if meeting.status == "pending":
                message = "Meeting is pending. Report will be available after the meeting is completed."
            elif meeting.status == "started":
                message = "Meeting is in progress. Report will be available after the meeting is completed."
            elif meeting.status == "completed":
                # Trigger analysis if meeting is completed but no reports exist
                analysis_service = AnalysisService()
                await analysis_service.enqueue_analysis(db, meeting_id)
                
                # Refresh meeting to get new report
                await db.refresh(meeting)
                
                if not meeting.reports:
                    message = "Report is being generated. Please try again in a few moments."
            elif meeting.status == "failed":
                message = "Meeting failed. No report available."
            else:
                message = "No report available for this meeting."
        
        return MeetingReportResponse(
            meeting_id=meeting.id,
            meeting_url=meeting.meeting_url,
            bot_id=meeting.bot_id,
            status=meeting.status,
            reports=meeting.reports,
            message=message,
            created_at=meeting.created_at,
            updated_at=meeting.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting meeting report: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{meeting_id}/transcripts", response_model=MeetingWithTranscripts)
async def get_meeting_transcripts(
    meeting_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get meeting transcripts (available during and after meeting)"""
    try:
        # Get meeting with transcript chunks
        result = await db.execute(
            select(Meeting)
            .options(selectinload(Meeting.transcript_chunks))
            .where(Meeting.id == meeting_id)
        )
        meeting = result.scalar_one_or_none()
        
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
        
        # Return transcripts regardless of meeting status
        # During meeting: real-time transcripts
        # After meeting: complete transcripts
        return MeetingWithTranscripts.model_validate(meeting)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting meeting transcripts: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") 


@router.get("/{meeting_id}/scorecard")
async def get_meeting_scorecard(
    meeting_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get meeting scorecard (AI-generated analysis)"""
    try:
        # Get meeting with reports and transcript chunks
        result = await db.execute(
            select(Meeting)
            .options(selectinload(Meeting.reports), selectinload(Meeting.transcript_chunks))
            .where(Meeting.id == meeting_id)
        )
        meeting = result.scalar_one_or_none()
        
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
        
        # Check if meeting has reports
        if not meeting.reports:
            if meeting.status == MeetingStatus.COMPLETED:
                # Check if there are transcript chunks before trying analysis
                if not meeting.transcript_chunks:
                    # No transcript data available - return error status
                    return {
                        "meeting_id": meeting_id,
                        "status": "no_data",
                        "message": "Meeting completed but no transcript data was captured. Cannot generate scorecard.",
                        "scorecard": None
                    }
                
                # Try to trigger analysis if meeting is completed, has transcript data, but no reports exist
                try:
                    analysis_service = AnalysisService()
                    analysis_result = await analysis_service.enqueue_analysis(db, meeting_id)
                    
                    if analysis_result:
                        # Analysis completed successfully
                        return {
                            "meeting_id": meeting_id,
                            "status": "available",
                            "message": "Scorecard generated successfully",
                            "scorecard": analysis_result
                        }
                    else:
                        # Analysis failed
                        return {
                            "meeting_id": meeting_id,
                            "status": "error",
                            "message": "Failed to generate scorecard. Please try again later.",
                            "scorecard": None
                        }
                        
                except Exception as e:
                    logger.error(f"Failed to generate scorecard for meeting {meeting_id}: {e}")
                    return {
                        "meeting_id": meeting_id,
                        "status": "error",
                        "message": "Failed to generate scorecard. Please try again later.",
                        "scorecard": None
                    }
            else:
                return {
                    "meeting_id": meeting_id,
                    "status": "unavailable",
                    "message": f"Scorecard not available for meeting with status '{meeting.status}'",
                    "scorecard": None
                }
        
        # Return the scorecard
        scorecard = meeting.reports[0].score if meeting.reports else None
        return {
            "meeting_id": meeting_id,
            "status": "available",
            "message": "Scorecard generated successfully",
            "scorecard": scorecard
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting scorecard for meeting {meeting_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") 