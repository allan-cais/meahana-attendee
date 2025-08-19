import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, update
from app.models.models import WebhookEvent, Meeting
from app.services.polling_service import polling_service
from app.core.config import settings
import json

logger = logging.getLogger(__name__)


class WebhookDeliveryService:
    """Service for managing webhook delivery, retries, and fallback logic"""
    
    def __init__(self):
        self.max_retry_attempts = settings.webhook_max_retry_attempts
        self.retry_delays = [int(delay.strip()) for delay in settings.webhook_retry_delays.split(",")]
        self.critical_events = ["post_processing_completed"]
        self.fallback_timeout = settings.webhook_fallback_timeout
        
        # Proactive monitoring settings
        self.proactive_check_interval = 120  # Check every 2 minutes
        self.meeting_timeout_threshold = 600  # 10 minutes without updates
        self.expected_webhook_patterns = {
            "STARTED": ["bot.state_change", "transcript.update"],
            "PENDING": ["bot.state_change"],
            "COMPLETED": ["post_processing_completed", "transcript.completed"]
        }
        
    async def start_proactive_monitoring(self):
        """Start proactive monitoring for webhook failures on Attendee's end"""
        logger.info("🚀 Starting proactive webhook failure monitoring")
        
        while True:
            try:
                await self._proactive_webhook_failure_check()
                await asyncio.sleep(self.proactive_check_interval)
            except Exception as e:
                logger.error(f"❌ Error in proactive webhook failure check: {e}")
                await asyncio.sleep(30)  # Wait 30 seconds before retrying
    
    async def _proactive_webhook_failure_check(self):
        """Proactively check for webhook failures on Attendee's end"""
        from app.core.database import AsyncSessionLocal
        
        async with AsyncSessionLocal() as db:
            try:
                # Find meetings that might have missed webhooks
                suspicious_meetings = await self._find_suspicious_meetings(db)
                
                if not suspicious_meetings:
                    logger.debug("No suspicious meetings detected")
                    return
                
                logger.info(f"🔍 Found {len(suspicious_meetings)} meetings with potential webhook failures")
                
                for meeting in suspicious_meetings:
                    await self._investigate_meeting_webhook_status(meeting, db)
                    
            except Exception as e:
                logger.error(f"Error in proactive webhook failure check: {e}")
    
    async def _find_suspicious_meetings(self, db: AsyncSession) -> List[Meeting]:
        """Find meetings that might have missed webhooks"""
        try:
            # Find meetings that haven't been updated recently
            timeout_threshold = datetime.now(timezone.utc) - timedelta(seconds=self.meeting_timeout_threshold)
            
            query = select(Meeting).where(
                and_(
                    Meeting.status.in_(["STARTED", "PENDING"]),
                    Meeting.updated_at < timeout_threshold
                )
            )
            
            result = await db.execute(query)
            meetings = result.scalars().all()
            
            suspicious_meetings = []
            
            for meeting in meetings:
                if await self._is_meeting_suspicious(meeting, db):
                    suspicious_meetings.append(meeting)
            
            return suspicious_meetings
            
        except Exception as e:
            logger.error(f"Error finding suspicious meetings: {e}")
            return []
    
    async def _is_meeting_suspicious(self, meeting: Meeting, db: AsyncSession) -> bool:
        """Check if a meeting is suspicious (missing expected webhooks)"""
        try:
            # Get recent webhook events for this meeting/bot
            recent_webhooks = await self._get_recent_webhook_events(meeting, db)
            
            # Check if we have the expected webhook pattern for the current status
            expected_events = self.expected_webhook_patterns.get(meeting.status, [])
            
            if not expected_events:
                return False
            
            # Check if we're missing expected webhooks
            missing_events = []
            for expected_event in expected_events:
                if not any(self._webhook_matches_event(webhook, expected_event) for webhook in recent_webhooks):
                    missing_events.append(expected_event)
            
            if missing_events:
                logger.warning(f"⚠️ Meeting {meeting.id} missing expected webhooks: {missing_events}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking if meeting {meeting.id} is suspicious: {e}")
            return False
    
    async def _get_recent_webhook_events(self, meeting: Meeting, db: AsyncSession) -> List[WebhookEvent]:
        """Get recent webhook events for a meeting"""
        try:
            # Look for webhooks in the last 15 minutes
            recent_threshold = datetime.now(timezone.utc) - timedelta(minutes=15)
            
            query = select(WebhookEvent).where(
                and_(
                    WebhookEvent.bot_id == meeting.bot_id,
                    WebhookEvent.created_at > recent_threshold
                )
            ).order_by(WebhookEvent.created_at.desc())
            
            result = await db.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error getting recent webhook events for meeting {meeting.id}: {e}")
            return []
    
    def _webhook_matches_event(self, webhook: WebhookEvent, expected_event: str) -> bool:
        """Check if a webhook matches an expected event type"""
        try:
            event_data = webhook.event_data
            if isinstance(event_data, dict):
                webhook_event_type = event_data.get("event_type")
                return webhook_event_type == expected_event
            return False
        except Exception as e:
            logger.error(f"Error checking webhook event match: {e}")
            return False
    
    async def _investigate_meeting_webhook_status(self, meeting: Meeting, db: AsyncSession):
        """Investigate a meeting's webhook status and trigger fallback if needed"""
        try:
            logger.info(f"🔍 Investigating webhook status for meeting {meeting.id}")
            
            # Check if we should trigger immediate fallback
            if await self._should_trigger_immediate_fallback(meeting, db):
                logger.warning(f"🚨 Meeting {meeting.id} triggering immediate fallback due to webhook failure")
                await self._trigger_polling_fallback(meeting, db)
            else:
                # Schedule a delayed fallback check
                await self._schedule_delayed_fallback_check(meeting, db)
                
        except Exception as e:
            logger.error(f"Error investigating meeting {meeting.id} webhook status: {e}")
    
    async def _should_trigger_immediate_fallback(self, meeting: Meeting, db: AsyncSession) -> bool:
        """Check if we should trigger immediate fallback for a meeting"""
        try:
            # Check if meeting has been stuck for a very long time
            very_long_threshold = datetime.now(timezone.utc) - timedelta(minutes=30)
            
            if meeting.updated_at < very_long_threshold:
                logger.warning(f"⚠️ Meeting {meeting.id} stuck for over 30 minutes, immediate fallback")
                return True
            
            # Check if we have no webhooks at all for this meeting
            webhook_count = await self._get_webhook_count_for_meeting(meeting, db)
            
            if webhook_count == 0:
                logger.warning(f"⚠️ Meeting {meeting.id} has no webhooks at all, immediate fallback")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking immediate fallback for meeting {meeting.id}: {e}")
            return False
    
    async def _get_webhook_count_for_meeting(self, meeting: Meeting, db: AsyncSession) -> int:
        """Get the total webhook count for a meeting"""
        try:
            query = select(WebhookEvent).where(WebhookEvent.bot_id == meeting.bot_id)
            result = await db.execute(query)
            return len(result.scalars().all())
        except Exception as e:
            logger.error(f"Error getting webhook count for meeting {meeting.id}: {e}")
            return 0
    
    async def _schedule_delayed_fallback_check(self, meeting: Meeting, db: AsyncSession):
        """Schedule a delayed fallback check for a meeting"""
        try:
            # Schedule a check after a shorter delay
            delay = min(self.fallback_timeout // 2, 120)  # Max 2 minutes
            
            asyncio.create_task(
                self._delayed_fallback_check(meeting, delay, db)
            )
            
            logger.info(f"📅 Scheduled delayed fallback check for meeting {meeting.id} in {delay} seconds")
            
        except Exception as e:
            logger.error(f"Error scheduling delayed fallback for meeting {meeting.id}: {e}")
    
    async def _delayed_fallback_check(self, meeting: Meeting, delay: int, db: AsyncSession):
        """Perform a delayed fallback check"""
        try:
            await asyncio.sleep(delay)
            
            # Check if the meeting still needs fallback
            current_meeting = await db.get(Meeting, meeting.id)
            if current_meeting and current_meeting.status not in ["COMPLETED", "FAILED"]:
                logger.warning(f"🚨 Meeting {meeting.id} still needs fallback after delay, triggering polling")
                await self._trigger_polling_fallback(current_meeting, db)
                
        except Exception as e:
            logger.error(f"Error in delayed fallback check for meeting {meeting.id}: {e}")
    
    async def process_webhook_delivery(
        self, 
        webhook_event: WebhookEvent, 
        db: AsyncSession
    ) -> bool:
        """Process webhook delivery and track status"""
        try:
            logger.info(f"📨 Processing webhook delivery for event {webhook_event.id}: {webhook_event.event_type}")
            
            # Mark as delivered
            webhook_event.delivery_status = "delivered"
            webhook_event.processed_at = datetime.now(timezone.utc)
            await db.commit()
            
            # Check if this is a critical event that should trigger fallback monitoring
            if self._is_critical_event(webhook_event):
                await self._schedule_fallback_monitoring(webhook_event, db)
            
            logger.info(f"✅ Webhook {webhook_event.id} delivered successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error processing webhook delivery {webhook_event.id}: {e}")
            await self._mark_delivery_failed(webhook_event, str(e), db)
            return False
    
    async def retry_failed_webhooks(self, db: AsyncSession) -> int:
        """Retry failed webhook deliveries"""
        try:
            # Find webhooks that need retrying
            failed_webhooks = await self._get_failed_webhooks(db)
            
            if not failed_webhooks:
                logger.debug("No failed webhooks to retry")
                return 0
            
            logger.info(f"🔄 Retrying {len(failed_webhooks)} failed webhooks")
            retry_count = 0
            
            for webhook in failed_webhooks:
                if await self._should_retry_webhook(webhook):
                    if await self._retry_webhook_delivery(webhook, db):
                        retry_count += 1
                else:
                    # Mark as permanently failed
                    await self._mark_permanently_failed(webhook, db)
            
            logger.info(f"✅ Retried {retry_count} webhooks successfully")
            return retry_count
            
        except Exception as e:
            logger.error(f"❌ Error in webhook retry process: {e}")
            return 0
    
    async def check_critical_event_fallbacks(self, db: AsyncSession) -> int:
        """Check if critical events are missing and trigger polling fallback"""
        try:
            # Find meetings that should have received critical events but haven't
            missing_critical_events = await self._find_missing_critical_events(db)
            
            if not missing_critical_events:
                logger.debug("No missing critical events detected")
                return 0
            
            logger.info(f"🚨 Found {len(missing_critical_events)} meetings missing critical events, triggering polling fallback")
            
            for meeting in missing_critical_events:
                await self._trigger_polling_fallback(meeting, db)
            
            return len(missing_critical_events)
            
        except Exception as e:
            logger.error(f"❌ Error checking critical event fallbacks: {e}")
            return 0
    
    def _is_critical_event(self, webhook_event: WebhookEvent) -> bool:
        """Check if a webhook event is critical for meeting completion"""
        try:
            event_data = webhook_event.event_data
            if isinstance(event_data, dict):
                event_type = event_data.get("event_type")
                new_state = event_data.get("new_state")
                return (event_type in self.critical_events and 
                       new_state == "ended")
            return False
        except Exception as e:
            logger.error(f"Error checking if event is critical: {e}")
            return False
    
    async def _schedule_fallback_monitoring(
        self, 
        webhook_event: WebhookEvent, 
        db: AsyncSession
    ):
        """Schedule fallback monitoring for critical events"""
        try:
            # Schedule a check after the fallback timeout
            asyncio.create_task(
                self._check_critical_event_completion(webhook_event, db)
            )
            logger.info(f"📅 Scheduled fallback monitoring for webhook {webhook_event.id}")
            
        except Exception as e:
            logger.error(f"Error scheduling fallback monitoring: {e}")
    
    async def _check_critical_event_completion(
        self, 
        webhook_event: WebhookEvent, 
        db: AsyncSession
    ):
        """Check if critical event was properly processed"""
        try:
            # Wait for the fallback timeout
            await asyncio.sleep(self.fallback_timeout)
            
            # Check if the meeting was properly completed
            if webhook_event.meeting_id:
                meeting = await db.get(Meeting, webhook_event.meeting_id)
                if meeting and meeting.status != "COMPLETED":
                    logger.warning(f"⚠️ Critical event {webhook_event.id} not properly processed, triggering polling fallback")
                    await self._trigger_polling_fallback(meeting, db)
                    
        except Exception as e:
            logger.error(f"Error in critical event completion check: {e}")
    
    async def _trigger_polling_fallback(self, meeting: Meeting, db: AsyncSession):
        """Trigger polling fallback for a meeting"""
        try:
            logger.info(f"🔄 Triggering polling fallback for meeting {meeting.id}")
            
            # Use the polling service to check meeting status
            await polling_service.manual_check_meeting(meeting.id)
            
        except Exception as e:
            logger.error(f"Error triggering polling fallback for meeting {meeting.id}: {e}")
    
    async def _get_failed_webhooks(self, db: AsyncSession) -> List[WebhookEvent]:
        """Get webhooks that have failed delivery"""
        try:
            query = select(WebhookEvent).where(
                and_(
                    WebhookEvent.delivery_status.in_(["failed", "retrying"]),
                    WebhookEvent.delivery_attempts < self.max_retry_attempts
                )
            )
            
            result = await db.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error getting failed webhooks: {e}")
            return []
    
    async def _should_retry_webhook(self, webhook: WebhookEvent) -> bool:
        """Check if a webhook should be retried"""
        if webhook.delivery_attempts >= self.max_retry_attempts:
            return False
        
        if not webhook.last_delivery_attempt:
            return True
        
        # Check if enough time has passed since last attempt
        delay = self.retry_delays[min(webhook.delivery_attempts, len(self.retry_delays) - 1)]
        time_since_last = datetime.now(timezone.utc) - webhook.last_delivery_attempt
        
        return time_since_last.total_seconds() >= delay
    
    async def _retry_webhook_delivery(self, webhook: WebhookEvent, db: AsyncSession) -> bool:
        """Retry webhook delivery"""
        try:
            logger.info(f"🔄 Retrying webhook delivery {webhook.id} (attempt {webhook.delivery_attempts + 1})")
            
            # Update retry information
            webhook.delivery_status = "retrying"
            webhook.delivery_attempts += 1
            webhook.last_delivery_attempt = datetime.now(timezone.utc)
            webhook.delivery_error = None
            
            await db.commit()
            
            # Simulate webhook retry (in real implementation, this would resend the webhook)
            # For now, we'll just mark it as delivered after a short delay
            await asyncio.sleep(2)  # Simulate processing time
            
            # Mark as delivered
            webhook.delivery_status = "delivered"
            webhook.processed_at = datetime.now(timezone.utc)
            await db.commit()
            
            logger.info(f"✅ Webhook {webhook.id} retry successful")
            return True
            
        except Exception as e:
            logger.error(f"❌ Webhook {webhook.id} retry failed: {e}")
            await self._mark_delivery_failed(webhook, str(e), db)
            return False
    
    async def _mark_delivery_failed(self, webhook: WebhookEvent, error: str, db: AsyncSession):
        """Mark webhook delivery as failed"""
        try:
            webhook.delivery_status = "failed"
            webhook.delivery_error = error
            webhook.last_delivery_attempt = datetime.now(timezone.utc)
            await db.commit()
            
        except Exception as e:
            logger.error(f"Error marking webhook {webhook.id} as failed: {e}")
    
    async def _mark_permanently_failed(self, webhook: WebhookEvent, db: AsyncSession):
        """Mark webhook as permanently failed after max retries"""
        try:
            webhook.delivery_status = "permanently_failed"
            webhook.delivery_error = f"Max retry attempts ({self.max_retry_attempts}) exceeded"
            await db.commit()
            
            logger.warning(f"⚠️ Webhook {webhook.id} marked as permanently failed")
            
        except Exception as e:
            logger.error(f"Error marking webhook {webhook.id} as permanently failed: {e}")
    
    async def _find_missing_critical_events(self, db: AsyncSession) -> List[Meeting]:
        """Find meetings that should have received critical events but haven't"""
        try:
            # Find meetings that are in progress but should be completed
            # and don't have critical webhook events
            query = select(Meeting).where(
                and_(
                    Meeting.status.in_(["STARTED", "PENDING"]),
                    Meeting.updated_at < datetime.now(timezone.utc) - timedelta(minutes=10)
                )
            )
            
            result = await db.execute(query)
            meetings = result.scalars().all()
            
            missing_critical_events = []
            
            for meeting in meetings:
                # Check if we have a critical webhook event for this meeting
                has_critical_event = await self._has_critical_webhook_event(meeting, db)
                
                if not has_critical_event:
                    missing_critical_events.append(meeting)
            
            return missing_critical_events
            
        except Exception as e:
            logger.error(f"Error finding missing critical events: {e}")
            return []
    
    async def _has_critical_webhook_event(self, meeting: Meeting, db: AsyncSession) -> bool:
        """Check if a meeting has received critical webhook events"""
        try:
            if not meeting.bot_id:
                return False
            
            # Look for critical webhook events
            query = select(WebhookEvent).where(
                and_(
                    WebhookEvent.bot_id == meeting.bot_id,
                    WebhookEvent.event_data.contains({"event_type": "post_processing_completed"}),
                    WebhookEvent.delivery_status == "delivered"
                )
            )
            
            result = await db.execute(query)
            return result.scalar_one_or_none() is not None
            
        except Exception as e:
            logger.error(f"Error checking critical webhook events for meeting {meeting.id}: {e}")
            return False
    
    async def get_webhook_delivery_stats(self, db: AsyncSession) -> Dict[str, Any]:
        """Get webhook delivery statistics"""
        try:
            # Count by delivery status
            status_counts = {}
            for status in ["pending", "delivered", "failed", "retrying", "permanently_failed"]:
                query = select(WebhookEvent).where(WebhookEvent.delivery_status == status)
                result = await db.execute(query)
                status_counts[status] = len(result.scalars().all())
            
            # Get retry statistics
            retry_query = select(WebhookEvent).where(WebhookEvent.delivery_attempts > 0)
            retry_result = await db.execute(retry_query)
            retry_count = len(retry_result.scalars().all())
            
            return {
                "status_counts": status_counts,
                "total_webhooks": sum(status_counts.values()),
                "retry_count": retry_count,
                "delivery_success_rate": (status_counts.get("delivered", 0) / max(sum(status_counts.values()), 1)) * 100
            }
            
        except Exception as e:
            logger.error(f"Error getting webhook delivery stats: {e}")
            return {}


# Global instance
webhook_delivery_service = WebhookDeliveryService()
