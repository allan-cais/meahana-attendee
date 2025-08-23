from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.webhook_service import WebhookService
from app.schemas.schemas import WebhookPayload
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook", tags=["webhooks"])


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
            "message": "This is the global webhook URL (for project-level webhooks)",
            "note": "For bot-level webhooks (recommended), each bot specifies its own webhook URL during creation",
            "instructions": [
                "1. For bot-level webhooks: Set webhook_base_url in bot config (e.g., your ngrok URL)",
                "2. Bot-level webhooks are automatically created when bots are created via API",
                "3. Select triggers: bot.state_change, transcript.update, chat_messages.update, participant_events.join_leave"
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
        result = await WebhookService.process_webhook(payload, db, background_tasks)
        return result
        
    except Exception as e:
        logger.error(f"Error processing Attendee webhook: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/attendee")
async def handle_attendee_webhook(
    payload: WebhookPayload,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Handle webhook events from Attendee API"""
    try:
        result = await WebhookService.process_webhook(payload, db, background_tasks)
        return result
        
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
                    WebhookService.process_webhook,
                    payload,
                    db,
                    background_tasks
                )
                
                retry_count += 1
                # Retrying webhook
                
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


 