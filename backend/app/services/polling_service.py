import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models.models import Meeting, WebhookEvent
from app.services.bot_service import BotService
from app.services.analysis_service import AnalysisService
from app.services.transcript_service import TranscriptService
from app.core.config import settings
import httpx

logger = logging.getLogger(__name__)


class PollingService:
    """Service for polling Attendee API to check meeting status and process transcripts as backup"""
    
    def __init__(self):
        self.is_running = False
        self.polling_interval = settings.polling_interval
        self.max_retries = settings.polling_max_retries
        self.retry_delay = settings.polling_retry_delay
        
    async def start_polling(self):
        """Start the polling service"""
        if self.is_running:
            logger.info("Polling service already running")
            return
            
        self.is_running = True
        logger.info("🚀 Starting polling service for meeting status checks")
        
        while self.is_running:
            try:
                await self._poll_completed_meetings()
                await asyncio.sleep(self.polling_interval)
            except Exception as e:
                logger.error(f"❌ Error in polling service: {e}")
                await asyncio.sleep(self.retry_delay)
    
    async def stop_polling(self):
        """Stop the polling service"""
        self.is_running = False
        logger.info("🛑 Polling service stopped")
    
    async def _poll_completed_meetings(self):
        """Poll for meetings that should be completed but haven't been processed"""
        from app.core.database import AsyncSessionLocal
        
        async with AsyncSessionLocal() as db:
            try:
                # First check if we have missing critical events that require polling fallback
                from app.services.webhook_delivery_service import webhook_delivery_service
                missing_critical_events = await webhook_delivery_service.check_critical_event_fallbacks(db)
                
                if missing_critical_events > 0:
                    logger.info(f"🚨 Polling fallback triggered for {missing_critical_events} meetings with missing critical events")
                    return  # Don't do general polling if we're handling critical event fallbacks
                
                # Only do general polling if no critical events are missing
                pending_meetings = await self._get_pending_meetings(db)
                
                if not pending_meetings:
                    logger.debug("No pending meetings to check")
                    return
                
                logger.info(f"🔍 Checking {len(pending_meetings)} pending meetings for completion status")
                
                for meeting in pending_meetings:
                    try:
                        await self._check_meeting_status(db, meeting)
                    except Exception as e:
                        logger.error(f"❌ Error checking meeting {meeting.id}: {e}")
                        continue
                        
            except Exception as e:
                logger.error(f"❌ Error in meeting status polling: {e}")
    
    async def _get_pending_meetings(self, db: AsyncSession) -> List[Meeting]:
        """Get meetings that are in progress and might be completed"""
        try:
            # Find meetings that are in progress and haven't been updated recently
            # This helps catch meetings where webhooks failed
            cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=10)  # Check meetings older than 10 minutes
            
            query = select(Meeting).where(
                and_(
                    Meeting.status.in_(["PENDING", "STARTED"]),
                    Meeting.updated_at < cutoff_time
                )
            )
            
            result = await db.execute(query)
            meetings = result.scalars().all()
            
            return meetings
            
        except Exception as e:
            logger.error(f"❌ Error getting pending meetings: {e}")
            return []
    
    async def _check_meeting_status(self, db: AsyncSession, meeting: Meeting):
        """Check the status of a specific meeting via Attendee API"""
        try:
            if not meeting.bot_id:
                logger.warning(f"⚠️ Meeting {meeting.id} has no bot_id, skipping")
                return
            
            logger.info(f"🔍 Checking status for meeting {meeting.id} (bot: {meeting.bot_id})")
            
            # Get bot status from Attendee API
            bot_status = await self._get_bot_status(meeting.bot_id)
            
            if not bot_status:
                logger.warning(f"⚠️ Could not get bot status for {meeting.bot_id}")
                return
            
            current_state = bot_status.get("state")
            logger.info(f"📊 Bot {meeting.bot_id} current state: {current_state}")
            
            # Check if meeting is completed
            if current_state == "ended":
                await self._handle_completed_meeting(db, meeting, bot_status)
            elif current_state in ["failed", "error"]:
                await self._handle_failed_meeting(db, meeting, bot_status)
            elif current_state in ["post_processing"]:
                # Check if post-processing has been running too long
                await self._check_post_processing_timeout(db, meeting, bot_status)
            else:
                logger.debug(f"📊 Meeting {meeting.id} still in progress: {current_state}")
                
        except Exception as e:
            logger.error(f"❌ Error checking meeting {meeting.id} status: {e}")
    
    async def _get_bot_status(self, bot_id: str) -> Optional[dict]:
        """Get bot status from Attendee API"""
        try:
            headers = {
                "Authorization": f"Token {settings.attendee_api_key}",
                "Content-Type": "application/json"
            }
            
            url = f"{settings.attendee_api_base_url}/api/v1/bots/{bot_id}"
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=headers)
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.warning(f"⚠️ Failed to get bot status: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Error getting bot status for {bot_id}: {e}")
            return None
    
    async def _handle_completed_meeting(self, db: AsyncSession, meeting: Meeting, bot_status: dict):
        """Handle a meeting that has been completed"""
        try:
            logger.info(f"🎉 Meeting {meeting.id} completed, updating status and processing transcript")
            
            # Update meeting status
            await BotService.update_meeting_status(db, meeting, "COMPLETED")
            
            # Check if we already have a webhook event for this completion
            existing_webhook = await self._check_existing_webhook(db, meeting.bot_id, "post_processing_completed")
            
            if not existing_webhook:
                logger.info(f"📝 No webhook event found for completion, creating one manually")
                await self._create_webhook_event(db, meeting, bot_status, "post_processing_completed")
            
            # Process transcript and trigger analysis
            await self._process_completed_meeting(db, meeting)
            
        except Exception as e:
            logger.error(f"❌ Error handling completed meeting {meeting.id}: {e}")
    
    async def _handle_failed_meeting(self, db: AsyncSession, meeting: Meeting, bot_status: dict):
        """Handle a meeting that has failed"""
        try:
            logger.info(f"❌ Meeting {meeting.id} failed, updating status")
            
            # Update meeting status
            await BotService.update_meeting_status(db, meeting, "FAILED")
            
            # Create webhook event for failure
            await self._create_webhook_event(db, meeting, bot_status, "bot.failed")
            
        except Exception as e:
            logger.error(f"❌ Error handling failed meeting {meeting.id}: {e}")
    
    async def _check_post_processing_timeout(self, db: AsyncSession, meeting: Meeting, bot_status: dict):
        """Check if post-processing has been running too long"""
        try:
            # Check if post-processing has been running for more than 30 minutes
            post_processing_start = meeting.updated_at
            timeout_threshold = datetime.now(timezone.utc) - timedelta(minutes=30)
            
            if post_processing_start < timeout_threshold:
                logger.warning(f"⚠️ Meeting {meeting.id} post-processing timeout, checking status")
                
                # Force a status check
                await self._check_meeting_status(db, meeting)
                
        except Exception as e:
            logger.error(f"❌ Error checking post-processing timeout for meeting {meeting.id}: {e}")
    
    async def _check_existing_webhook(self, db: AsyncSession, bot_id: str, event_type: str) -> Optional[WebhookEvent]:
        """Check if a webhook event already exists for this bot and event type"""
        try:
            query = select(WebhookEvent).where(
                and_(
                    WebhookEvent.event_data.contains({"bot_id": bot_id}),
                    WebhookEvent.event_type == event_type
                )
            )
            
            result = await db.execute(query)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"❌ Error checking existing webhook: {e}")
            return None
    
    async def _create_webhook_event(self, db: AsyncSession, meeting: Meeting, bot_status: dict, event_type: str):
        """Create a webhook event manually when webhook fails"""
        try:
            # Create webhook event data
            event_data = {
                "bot_id": meeting.bot_id,
                "meeting_url": meeting.meeting_url,
                "new_state": bot_status.get("state"),
                "old_state": meeting.status,
                "event_type": event_type,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "event_metadata": bot_status.get("metadata", {})
            }
            
            webhook_event = WebhookEvent(
                event_type=event_type,
                event_data=event_data,
                raw_payload={"data": event_data},
                meeting_id=meeting.id,
                processed="true"  # Mark as processed since we're handling it
            )
            
            db.add(webhook_event)
            await db.commit()
            
            logger.info(f"📝 Created manual webhook event for meeting {meeting.id}: {event_type}")
            
        except Exception as e:
            logger.error(f"❌ Error creating webhook event: {e}")
    
    async def _process_completed_meeting(self, db: AsyncSession, meeting: Meeting):
        """Process transcript and trigger analysis for completed meeting"""
        try:
            logger.info(f"🔄 Processing completed meeting {meeting.id}")
            
            # Fetch transcript from Attendee API
            transcript_service = TranscriptService()
            transcript_fetched = await transcript_service.fetch_full_transcript(db, meeting)
            
            if transcript_fetched:
                logger.info(f"📝 Transcript fetched for meeting {meeting.id}")
                
                # Trigger analysis
                analysis_service = AnalysisService()
                await analysis_service.enqueue_analysis(db, meeting.id)
                
                logger.info(f"🧠 Analysis enqueued for meeting {meeting.id}")
            else:
                logger.warning(f"⚠️ Could not fetch transcript for meeting {meeting.id}")
                
        except Exception as e:
            logger.error(f"❌ Error processing completed meeting {meeting.id}: {e}")
    
    async def manual_check_meeting(self, meeting_id: int):
        """Manually check a specific meeting (for testing/debugging)"""
        from app.core.database import AsyncSessionLocal
        
        async with AsyncSessionLocal() as db:
            try:
                meeting = await db.get(Meeting, meeting_id)
                if not meeting:
                    logger.error(f"❌ Meeting {meeting_id} not found")
                    return False
                
                await self._check_meeting_status(db, meeting)
                return True
                
            except Exception as e:
                logger.error(f"❌ Error in manual meeting check: {e}")
                return False


# Global instance
polling_service = PollingService()
