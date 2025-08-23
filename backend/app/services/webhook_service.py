import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.models import Meeting, WebhookEvent, TranscriptChunk
from app.schemas.schemas import WebhookPayload
from app.core.config import settings
from fastapi import BackgroundTasks
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import json

logger = logging.getLogger(__name__)


class WebhookService:
    @staticmethod
    def get_webhook_url() -> Optional[str]:
        """Get the global webhook URL for the application"""
        # This method is mainly used for debugging and documentation purposes
        
        # Production: Use configured webhook base URL if available
        if settings.is_production and settings.webhook_base_url:
            webhook_url = f"{settings.webhook_base_url.rstrip('/')}/webhook"
            return webhook_url
        
        # Development: Show available options
        if settings.webhook_base_url:
            webhook_url = f"{settings.webhook_base_url.rstrip('/')}/webhook"
            return webhook_url
        
        return None

    @staticmethod
    async def process_webhook(
        payload: WebhookPayload, 
        db: AsyncSession, 
        background_tasks: BackgroundTasks
    ) -> dict:
        """Process webhook payload - Production-ready version"""
        try:
            # Start transaction
            async with db.begin():
                # Store webhook event
                event_type = payload.get_event_type()
                bot_id = payload.get_bot_id()
                
                webhook_event = WebhookEvent(
                    event_type=event_type,
                    bot_id=bot_id,
                    event_data=payload.data,
                    raw_payload=payload.model_dump(),
                    meeting_id=None,
                    processed="false"
                )
                
                db.add(webhook_event)
                await db.flush()  # Get ID without committing
                
                # Process webhook delivery tracking
                from app.services.webhook_delivery_service import webhook_delivery_service
                await webhook_delivery_service.process_webhook_delivery(webhook_event, db)
                
                # Link webhook to meeting
                await WebhookService._link_webhook_to_meeting(webhook_event, payload, db)
                
                # Production-ready: If no meeting exists for this webhook, fail fast
                if not webhook_event.meeting_id:
                    logger.error(f"Webhook event {webhook_event.id} cannot be linked to any meeting. This indicates a system error.")
                    raise ValueError(f"Webhook event {webhook_event.id} has no associated meeting. Bot creation may have failed.")
                
                # Handle different event types
                await WebhookService._process_event_by_type(event_type, payload, db, background_tasks)
                
                # Mark webhook as processed
                webhook_event.processed = "true"
                webhook_event.processed_at = datetime.now(timezone.utc)
                
                return {"status": "processed", "event_type": event_type}
                
        except Exception as e:
            logger.error(f"Error processing webhook event {event_type}: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Mark webhook as failed - don't commit here since we're in a transaction
            if 'webhook_event' in locals():
                webhook_event.processed = "false"
                webhook_event.delivery_status = "failed"
                webhook_event.delivery_error = str(e)
                # Don't commit here - the transaction will be rolled back automatically
            
            raise  # Re-raise to trigger the 500 response

    @staticmethod
    def _has_transcript_data(payload: WebhookPayload) -> bool:
        """Check if payload contains transcript data"""
        data = payload.data
        # Check if payload has transcription data
        if data.get("transcription") and data["transcription"].get("transcript"):
            return True
        # Check if payload has direct text field
        if data.get("text"):
            return True
        return False

    @staticmethod
    async def _link_webhook_to_meeting(webhook_event, payload: WebhookPayload, db: AsyncSession):
        """Link webhook event to a meeting for proper cascade deletion"""
        from app.services.bot_service import BotService
        
        if webhook_event.meeting_id:
            # Already linked
            return
        
        # Production-ready: Find meeting by bot_id or fail
        bot_id = payload.get_bot_id()
        if not bot_id:
            logger.error("Webhook has no bot_id. Cannot link to meeting.")
            return
        
        meeting = await BotService.get_meeting_by_bot_id(db, bot_id)
        if meeting:
            webhook_event.meeting_id = meeting.id
            # Don't commit here - let the main transaction handle it
        else:
            logger.error(f"No meeting found for bot {bot_id}. Bot creation may have failed.")
            # Don't create meetings automatically - this indicates a system error



    @staticmethod
    async def _process_event_by_type(
        event_type: str, 
        payload: WebhookPayload, 
        db: AsyncSession, 
        background_tasks: BackgroundTasks
    ):
        """Route webhook events to appropriate handlers based on event type"""
        from app.services.bot_service import BotService
        
        if event_type in ["bot.state_change", "bot.join_requested", "bot.joining", "bot.joined"]:
            await WebhookService._handle_bot_state_change(payload, db, background_tasks)
        elif event_type in ["bot.recording", "bot.started_recording"]:
            await WebhookService._handle_bot_recording(payload, db)
        elif event_type in ["bot.left", "bot.completed"]:
            await WebhookService._handle_bot_completed(payload, db, background_tasks)
        elif event_type in ["bot.failed"]:
            await WebhookService._handle_bot_failed(payload, db)
        elif event_type in ["transcript.update", "transcript.chunk"]:
            await WebhookService._handle_transcript_chunk(payload, db)
        elif event_type in ["transcript.completed"]:
            await WebhookService._handle_transcript_completed(payload, db, background_tasks)
        elif event_type in ["chat_messages.update"]:
            await WebhookService._handle_chat_message(payload, db)
        elif event_type in ["participant_events.join_leave"]:
            await WebhookService._handle_participant_event(payload, db)
        elif event_type == "post_processing_completed":
            await WebhookService._handle_post_processing_completed(payload, db, background_tasks)
        elif event_type == "unknown" and WebhookService._has_transcript_data(payload):
            await WebhookService._handle_transcript_chunk(payload, db)
        else:
            logger.warning(f"Unhandled webhook event: {event_type}")

    @staticmethod
    async def _handle_bot_state_change(
        payload: WebhookPayload, 
        db: AsyncSession, 
        background_tasks: BackgroundTasks
    ):
        """Handle bot state change events according to Attendee API specification"""
        from app.services.bot_service import BotService
        
        bot_id = payload.get_bot_id()
        data = payload.data
        
        # Extract state change information per Attendee API spec
        new_state = data.get("new_state")
        old_state = data.get("old_state")
        event_type = data.get("event_type")
        event_sub_type = data.get("event_sub_type")
        
        if new_state == "ended" and event_type == "post_processing_completed":
            # Bot has completed post-processing and meeting is ended
            meeting = await BotService.get_meeting_by_bot_id(db, bot_id)
            if meeting:
                # Update meeting status to completed
                await BotService.update_meeting_status(db, meeting, "completed")
                
                # Trigger analysis in background
                background_tasks.add_task(
                    WebhookService._fetch_transcript_and_analyze,
                    meeting.id,
                    bot_id
                )
        elif new_state in ["failed", "error"]:
            # Bot failed
            meeting = await BotService.get_meeting_by_bot_id(db, bot_id)
            if meeting:
                await BotService.update_meeting_status(db, meeting, "failed")
        elif new_state in ["staged", "join_requested", "joining", "joined_meeting", "joined_recording", "recording_permission_granted"]:
            # Bot is joining or in meeting
            meeting = await BotService.get_meeting_by_bot_id(db, bot_id)
            if meeting and meeting.status != "started":
                await BotService.update_meeting_status(db, meeting, "started")

    @staticmethod
    async def _handle_bot_recording(payload: WebhookPayload, db: AsyncSession):
        """Handle bot recording events"""
        from app.services.bot_service import BotService
        
        bot_id = payload.get_bot_id()
        
        meeting = await BotService.get_meeting_by_bot_id(db, bot_id)
        if meeting:
            await BotService.update_meeting_status(db, meeting, "started")

    @staticmethod
    async def _handle_bot_completed(
        payload: WebhookPayload, 
        db: AsyncSession, 
        background_tasks: BackgroundTasks
    ):
        """Handle bot completion events"""
        from app.services.bot_service import BotService
        
        bot_id = payload.get_bot_id()
        
        meeting = await BotService.get_meeting_by_bot_id(db, bot_id)
        if meeting:
            await BotService.update_meeting_status(db, meeting, "completed")
            
            # Trigger transcript fetch and analysis in background
            background_tasks.add_task(
                WebhookService._fetch_transcript_and_analyze,
                meeting.id,
                bot_id
            )
        else:
            logger.warning(f"No meeting found for completed bot {bot_id}")

    @staticmethod
    async def _handle_bot_failed(payload: WebhookPayload, db: AsyncSession):
        """Handle bot failure events"""
        from app.services.bot_service import BotService
        
        bot_id = payload.get_bot_id()
        
        meeting = await BotService.get_meeting_by_bot_id(db, bot_id)
        if meeting:
            await BotService.update_meeting_status(db, meeting, "failed")

    @staticmethod
    async def _handle_transcript_chunk(payload: WebhookPayload, db: AsyncSession):
        """Handle real-time transcript chunks"""
        from app.services.bot_service import BotService
        
        # Try to get bot_id first
        bot_id = payload.get_bot_id()
        
        # Find meeting using BotService
        meeting = await BotService.get_meeting_by_bot_id(db, bot_id)
        
        if not meeting:
            logger.warning(f"Could not find meeting for transcript webhook")
            return
        
        # Extract transcript data
        data = payload.data
        speaker = data.get("speaker") or data.get("speaker_name", "Unknown")
        text = data.get("text") or (data.get("transcription", {}) or {}).get("transcript", "")
        timestamp_ms = data.get("timestamp_ms")
        timestamp_str = data.get("timestamp")
        confidence = data.get("confidence", "medium")
        
        if not text:
            logger.warning("Empty transcript text received")
            return
        
        # Parse timestamp
        try:
            if timestamp_ms:
                timestamp = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
            elif timestamp_str:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            else:
                timestamp = datetime.now(timezone.utc)
        except Exception as e:
            logger.warning(f"Failed to parse timestamp {timestamp_ms} or {timestamp_str}: {e}")
            timestamp = datetime.now(timezone.utc)
        
        # Store transcript chunk
        chunk = TranscriptChunk(
            meeting_id=meeting.id,
            speaker=speaker,
            text=text,
            timestamp=timestamp,
            confidence=confidence
        )
        
        db.add(chunk)
        # Don't commit here - let the main transaction handle it

    @staticmethod
    async def _handle_transcript_completed(
        payload: WebhookPayload, 
        db: AsyncSession, 
        background_tasks: BackgroundTasks
    ):
        """Handle transcript completion events"""
        from app.services.bot_service import BotService
        
        bot_id = payload.get_bot_id()
        
        meeting = await BotService.get_meeting_by_bot_id(db, bot_id)
        if meeting:
            # Trigger analysis in background
            background_tasks.add_task(
                WebhookService._fetch_transcript_and_analyze,
                meeting.id,
                bot_id
            )

    @staticmethod
    async def _handle_chat_message(payload: WebhookPayload, db: AsyncSession):
        """Handle chat message events"""
        bot_id = payload.get_bot_id()
        # TODO: Implement chat message storage if needed

    @staticmethod
    async def _handle_participant_event(payload: WebhookPayload, db: AsyncSession):
        """Handle participant join/leave events"""
        bot_id = payload.get_bot_id()
        data = payload.data
        event_type = data.get("event_type", "unknown")
        participant = data.get("participant", {})
        # TODO: Implement participant tracking if needed

    @staticmethod
    async def _handle_post_processing_completed(
        payload: WebhookPayload, 
        db: AsyncSession, 
        background_tasks: BackgroundTasks
    ):
        """Handle post-processing completed events"""
        from app.services.bot_service import BotService
        
        bot_id = payload.get_bot_id()
        if not bot_id:
            logger.error("Post-processing completed webhook has no bot_id. Cannot process.")
            raise ValueError("Post-processing completed webhook missing bot_id")
        
        # Production-ready: Find meeting by bot_id or fail
        meeting = await BotService.get_meeting_by_bot_id(db, bot_id)
        if not meeting:
            logger.error(f"No meeting found for bot {bot_id}. Bot creation may have failed.")
            raise ValueError(f"Meeting not found for bot {bot_id}")
        
        # Update meeting status to completed (don't commit - let main transaction handle it)
        await BotService.update_meeting_status(db, meeting, "completed", commit=False)
        
        # Trigger analysis in background
        background_tasks.add_task(
            WebhookService._fetch_transcript_and_analyze,
            meeting.id,
            bot_id
        )

    @staticmethod
    async def _fetch_transcript_and_analyze(meeting_id: int, bot_id: str):
        """Background task to fetch transcript and trigger analysis"""
        from app.core.database import AsyncSessionLocal
        from app.services.analysis_service import AnalysisService
        
        async with AsyncSessionLocal() as db:
            try:
                # Get meeting
                meeting = await db.get(Meeting, meeting_id)
                if not meeting:
                    logger.error(f"Meeting {meeting_id} not found in background task")
                    return
                
                # TODO: Fetch full transcript from Attendee API if needed
                # For now, we rely on real-time transcript chunks
                
                # Trigger analysis
                analysis_service = AnalysisService()
                await analysis_service.enqueue_analysis(db, meeting_id)
                
            except Exception as e:
                logger.error(f"Error in background transcript fetch and analysis: {e}")
                import traceback
                logger.error(f"Background task traceback: {traceback.format_exc()}") 