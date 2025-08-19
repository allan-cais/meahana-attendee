from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.webhook_service import WebhookService
from app.schemas.schemas import WebhookPayload
from app.core.config import settings
import hmac
import hashlib
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook", tags=["webhooks"])


@router.get("/debug")
async def get_webhook_debug_info(db: AsyncSession = Depends(get_db)):
    """Debug endpoint to see webhook events and bot statuses"""
    try:
        from sqlalchemy import select
        from app.models.models import WebhookEvent, Meeting
        
        # Get recent webhook events
        webhook_result = await db.execute(
            select(WebhookEvent)
            .order_by(WebhookEvent.created_at.desc())
            .limit(10)
        )
        webhook_events = webhook_result.scalars().all()
        
        # Get all meetings with their statuses
        meetings_result = await db.execute(
            select(Meeting)
            .order_by(Meeting.created_at.desc())
        )
        meetings = meetings_result.scalars().all()
        
        return {
            "webhook_events": [
                {
                    "id": event.id,
                    "event_type": event.event_type,
                    "meeting_id": event.meeting_id,
                    "bot_id": event.bot_id,
                    "created_at": event.created_at.isoformat(),
                    "event_data": event.event_data,
                    "raw_payload": event.raw_payload,
                    "processed": event.processed,
                    "processed_at": event.processed_at.isoformat() if event.processed_at else None
                }
                for event in webhook_events
            ],
            "meetings": [
                {
                    "id": meeting.id,
                    "bot_id": meeting.bot_id,
                    "status": meeting.status,
                    "meeting_url": meeting.meeting_url,
                    "created_at": meeting.created_at.isoformat(),
                    "updated_at": meeting.updated_at.isoformat()
                }
                for meeting in meetings
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting webhook debug info: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/url")
async def get_webhook_url():
    """Get the current webhook URL for copying to external services"""
    try:
        from app.services.webhook_service import WebhookService
        
        webhook_url = WebhookService.get_webhook_url()
        
        if not webhook_url:
            raise HTTPException(status_code=404, detail="No webhook URL configured")
        
        return {
            "webhook_url": webhook_url,
            "message": "Copy this URL to the Attendee API webhook configuration",
            "instructions": [
                "1. Go to the Attendee API Developer Portal",
                "2. Create a new webhook",
                "3. Paste this URL into the 'Webhook URL' field",
                "4. Select all triggers: bot.state_change, transcript.update, chat_messages.update, participant_events.join_leave",
                "5. Click 'Create'"
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting webhook URL: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/")
async def handle_webhook(
    payload: WebhookPayload,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Handle webhook events from Attendee API"""
    try:
        result = await WebhookService.handle_event(payload, db, background_tasks)
        return result
        
    except Exception as e:
        logger.error(f"Error processing Attendee webhook: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/attendee")
async def handle_attendee_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Handle webhook events from Attendee API with signature verification"""
    try:
        # Get the raw body for signature verification
        raw_body = await request.body()
        
        # Parse the JSON payload
        payload_dict = json.loads(raw_body)
        
        # Verify webhook signature if secret is configured
        if settings.webhook_secret:
            signature = request.headers.get("X-Webhook-Signature")
            if not signature or not verify_attendee_signature(raw_body, signature):
                raise HTTPException(status_code=401, detail="Invalid signature")
        
        # Convert to WebhookPayload
        payload = WebhookPayload(**payload_dict)
        
        # Handle the webhook event
        result = await WebhookService.handle_event(payload, db, background_tasks)
        
        return result
        
    except json.JSONDecodeError:
        logger.error("Invalid JSON payload")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    except Exception as e:
        logger.error(f"Error processing Attendee webhook: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/retry-failed")
async def retry_failed_webhooks(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Retry processing failed webhook events"""
    try:
        from sqlalchemy import select, update
        from app.models.models import WebhookEvent
        
        # Find failed webhooks
        result = await db.execute(
            select(WebhookEvent).where(
                WebhookEvent.processed == "false"
            ).order_by(WebhookEvent.created_at.desc())
        )
        failed_webhooks = result.scalars().all()
        
        if not failed_webhooks:
            return {"message": "No failed webhooks to retry", "count": 0}
        
        retry_count = 0
        for webhook in failed_webhooks:
            try:
                # Reset status for retry
                webhook.processed = "false"
                webhook.delivery_status = "pending"
                webhook.delivery_error = None
                await db.commit()
                
                # Re-process the webhook
                from app.services.webhook_service import WebhookService
                from app.schemas.schemas import WebhookPayload
                
                # Reconstruct payload from stored data
                payload = WebhookPayload(**webhook.raw_payload)
                
                # Process in background to avoid blocking
                background_tasks.add_task(
                    WebhookService.handle_event,
                    payload,
                    db,
                    background_tasks
                )
                
                retry_count += 1
                logger.info(f"Retrying webhook {webhook.id}: {webhook.event_type}")
                
            except Exception as e:
                logger.error(f"Error retrying webhook {webhook.id}: {e}")
                continue
        
        return {
            "message": f"Retry initiated for {retry_count} failed webhooks",
            "count": retry_count
        }
        
    except Exception as e:
        logger.error(f"Error in retry-failed endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retry webhooks: {str(e)}")


def verify_attendee_signature(raw_body: bytes, signature_header: str) -> bool:
    """Verify Attendee webhook signature"""
    try:
        if not settings.webhook_secret:
            return True
            
        # Calculate expected signature
        expected_signature = hmac.new(
            settings.webhook_secret.encode(),
            raw_body,
            hashlib.sha256
        ).hexdigest()
        
        # Compare signatures
        return hmac.compare_digest(f"sha256={expected_signature}", signature_header)
        
    except Exception as e:
        logger.error(f"Error verifying signature: {e}")
        return False 