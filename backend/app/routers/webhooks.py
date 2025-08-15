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
                    "bot_id": event.bot_id,
                    "created_at": event.created_at.isoformat(),
                    "event_data": event.event_data
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