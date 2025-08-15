import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.models import Meeting, WebhookEvent, TranscriptChunk
from app.schemas.schemas import WebhookPayload
from app.core.config import settings
from fastapi import BackgroundTasks
from typing import Dict, Any, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class WebhookService:
    @staticmethod
    def get_webhook_url() -> Optional[str]:
        """Get the appropriate webhook URL based on environment"""
        # Production: Use configured webhook base URL
        if settings.is_production and settings.webhook_base_url:
            webhook_url = f"{settings.webhook_base_url.rstrip('/')}/webhook"
            logger.info(f"🏭 Using production webhook URL: {webhook_url}")
            return webhook_url
        
        # Development: Use ngrok tunnel (returns complete webhook URL)
        if settings.should_use_ngrok:
            from app.services.ngrok_service import ngrok_service
            ngrok_webhook_url = ngrok_service.get_webhook_url()
            if ngrok_webhook_url:
                logger.info(f"🚇 Using ngrok webhook URL: {ngrok_webhook_url}")
                return ngrok_webhook_url
            else:
                logger.warning("🚫 Ngrok enabled but no tunnel URL available")
        
        # Fallback: Manual webhook base URL for development
        if settings.webhook_base_url:
            webhook_url = f"{settings.webhook_base_url.rstrip('/')}/webhook"
            logger.info(f"🔧 Using manual webhook URL: {webhook_url}")
            return webhook_url
        
        logger.warning("❌ No webhook URL configured - set WEBHOOK_BASE_URL or enable ngrok")
        return None

    @staticmethod
    async def handle_event(
        payload: WebhookPayload, 
        db: AsyncSession, 
        background_tasks: BackgroundTasks
    ) -> Dict[str, Any]:
        """Handle webhook events from Attendee API or legacy format"""
        
        # Get event type using the unified method
        event_type = payload.get_event_type()
        bot_id = payload.get_bot_id()
        
        logger.info(f"🔔 Processing webhook event: {event_type} for bot {bot_id}")
        logger.info(f"📦 Webhook payload data: {payload.data}")
        
        # Store webhook event
        webhook_event = WebhookEvent(
            event_type=event_type,
            event_data=payload.data,
            raw_payload=payload.model_dump(),
            bot_id=bot_id
        )
        
        db.add(webhook_event)
        await db.commit()
        await db.refresh(webhook_event)
        
        logger.info(f"💾 Stored webhook event {event_type} with ID {webhook_event.id}")
        
        # Handle different event types (both Attendee trigger format and legacy event format)
        if event_type in ["bot.state_change", "bot.join_requested", "bot.joining", "bot.joined"]:
            logger.info(f"🤖 Handling bot state change event: {event_type}")
            await WebhookService._handle_bot_state_change(payload, db, background_tasks)
        elif event_type in ["bot.recording", "bot.started_recording"]:
            logger.info(f"🎥 Handling bot recording event: {event_type}")
            await WebhookService._handle_bot_recording(payload, db)
        elif event_type in ["bot.left", "bot.completed"]:
            logger.info(f"✅ Handling bot completion event: {event_type}")
            await WebhookService._handle_bot_completed(payload, db, background_tasks)
        elif event_type in ["bot.failed"]:
            logger.info(f"❌ Handling bot failure event: {event_type}")
            await WebhookService._handle_bot_failed(payload, db)
        elif event_type in ["transcript.update", "transcript.chunk"]:
            logger.info(f"📝 Handling transcript update event: {event_type}")
            await WebhookService._handle_transcript_chunk(payload, db)
        elif event_type in ["transcript.completed"]:
            logger.info(f"🏁 Handling transcript completion event: {event_type}")
            await WebhookService._handle_transcript_completed(payload, db, background_tasks)
        elif event_type in ["chat_messages.update"]:
            logger.info(f"💬 Handling chat message event: {event_type}")
            await WebhookService._handle_chat_message(payload, db)
        elif event_type in ["participant_events.join_leave"]:
            logger.info(f"👥 Handling participant event: {event_type}")
            await WebhookService._handle_participant_event(payload, db)
        else:
            logger.warning(f"⚠️ Unhandled webhook event: {event_type}")
        
        logger.info(f"✅ Webhook event {event_type} processed successfully")
        return {"status": "processed", "event_type": event_type}

    @staticmethod
    async def _handle_bot_state_change(
        payload: WebhookPayload, 
        db: AsyncSession, 
        background_tasks: BackgroundTasks
    ):
        """Handle bot state change events"""
        from app.services.bot_service import BotService
        
        bot_id = payload.get_bot_id()
        data = payload.data
        new_status = data.get("status")
        
        logger.info(f"Bot {bot_id} state changed to: {new_status}")
        
        if new_status == "completed":
            # Bot has completed the meeting
            meeting = await BotService.get_meeting_by_bot_id(db, bot_id)
            if meeting:
                logger.info(f"Bot {bot_id} completed meeting {meeting.id}, updating status")
                
                # Update meeting status to completed
                await BotService.update_meeting_status(db, meeting, "completed")
                
                # Trigger analysis in background
                background_tasks.add_task(
                    WebhookService._fetch_transcript_and_analyze,
                    meeting.id,
                    bot_id
                )
                
                logger.info(f"Analysis triggered for completed meeting {meeting.id}")
        elif new_status == "failed":
            # Bot failed
            meeting = await BotService.get_meeting_by_bot_id(db, bot_id)
            if meeting:
                logger.info(f"Bot {bot_id} failed for meeting {meeting.id}, updating status")
                await BotService.update_meeting_status(db, meeting, "failed")

    @staticmethod
    async def _handle_bot_recording(payload: WebhookPayload, db: AsyncSession):
        """Handle bot recording events"""
        from app.services.bot_service import BotService
        
        bot_id = payload.get_bot_id()
        logger.info(f"Bot {bot_id} started recording")
        
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
        logger.info(f"🎯 Bot {bot_id} completed/left meeting")
        
        meeting = await BotService.get_meeting_by_bot_id(db, bot_id)
        if meeting:
            logger.info(f"📋 Found meeting {meeting.id} for completed bot {bot_id}")
            await BotService.update_meeting_status(db, meeting, "completed")
            logger.info(f"✅ Updated meeting {meeting.id} status to 'completed'")
            
            # Trigger transcript fetch and analysis in background
            logger.info(f"🚀 Scheduling background analysis for meeting {meeting.id}")
            background_tasks.add_task(
                WebhookService._fetch_transcript_and_analyze,
                meeting.id,
                bot_id
            )
            logger.info(f"📅 Background analysis task scheduled for meeting {meeting.id}")
        else:
            logger.warning(f"⚠️ No meeting found for completed bot {bot_id}")

    @staticmethod
    async def _handle_bot_failed(payload: WebhookPayload, db: AsyncSession):
        """Handle bot failure events"""
        from app.services.bot_service import BotService
        
        bot_id = payload.get_bot_id()
        logger.info(f"Bot {bot_id} failed")
        
        meeting = await BotService.get_meeting_by_bot_id(db, bot_id)
        if meeting:
            await BotService.update_meeting_status(db, meeting, "failed")

    @staticmethod
    async def _handle_transcript_chunk(payload: WebhookPayload, db: AsyncSession):
        """Handle real-time transcript chunks"""
        from app.services.bot_service import BotService
        
        bot_id = payload.get_bot_id()
        
        # Get meeting
        meeting = await BotService.get_meeting_by_bot_id(db, bot_id)
        if not meeting:
            logger.warning(f"Meeting not found for bot_id: {bot_id}")
            return
        
        # Extract transcript data
        data = payload.data
        logger.info(data)
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
            if timestamp_str:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            else:
                timestamp = datetime.utcnow()
        except Exception as e:
            logger.warning(f"Failed to parse timestamp {timestamp_str}: {e}")
            timestamp = datetime.utcnow()
        
        # Store transcript chunk
        chunk = TranscriptChunk(
            meeting_id=meeting.id,
            speaker=speaker,
            text=text,
            timestamp=timestamp,
            confidence=confidence
        )
        
        db.add(chunk)
        await db.commit()
        
        logger.info(f"Stored transcript chunk for meeting {meeting.id}: {speaker}: {text[:50]}...")

    @staticmethod
    async def _handle_transcript_completed(
        payload: WebhookPayload, 
        db: AsyncSession, 
        background_tasks: BackgroundTasks
    ):
        """Handle transcript completion events"""
        from app.services.bot_service import BotService
        
        bot_id = payload.get_bot_id()
        logger.info(f"Transcript completed for bot {bot_id}")
        
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
        logger.info(f"Chat message received for bot {bot_id}")
        # TODO: Implement chat message storage if needed

    @staticmethod
    async def _handle_participant_event(payload: WebhookPayload, db: AsyncSession):
        """Handle participant join/leave events"""
        bot_id = payload.get_bot_id()
        data = payload.data
        event_type = data.get("event_type", "unknown")
        participant = data.get("participant", {})
        logger.info(f"Participant event for bot {bot_id}: {event_type} - {participant}")
        # TODO: Implement participant tracking if needed

    @staticmethod
    async def _fetch_transcript_and_analyze(meeting_id: int, bot_id: str):
        """Background task to fetch transcript and trigger analysis"""
        from app.core.database import AsyncSessionLocal
        from app.services.analysis_service import AnalysisService
        
        logger.info(f"🔄 Starting background task for meeting {meeting_id}, bot {bot_id}")
        
        async with AsyncSessionLocal() as db:
            try:
                logger.info(f"📥 Fetching transcript and triggering analysis for meeting {meeting_id}")
                
                # Get meeting
                meeting = await db.get(Meeting, meeting_id)
                if not meeting:
                    logger.error(f"❌ Meeting {meeting_id} not found in background task")
                    return
                
                logger.info(f"📋 Found meeting {meeting_id} in background task: {meeting.meeting_url}")
                
                # TODO: Fetch full transcript from Attendee API if needed
                # For now, we rely on real-time transcript chunks
                
                # Trigger analysis
                logger.info(f"🧠 Triggering analysis service for meeting {meeting_id}")
                analysis_service = AnalysisService()
                await analysis_service.enqueue_analysis(db, meeting_id)
                
                logger.info(f"✅ Analysis enqueued successfully for meeting {meeting_id}")
                
            except Exception as e:
                logger.error(f"❌ Error in background transcript fetch and analysis: {e}")
                import traceback
                logger.error(f"📚 Background task traceback: {traceback.format_exc()}") 