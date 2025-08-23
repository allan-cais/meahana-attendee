from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.webhook_delivery_service import webhook_delivery_service
from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook-delivery", tags=["webhook-delivery"])


class WebhookDeliveryResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


@router.get("/stats", response_model=WebhookDeliveryResponse)
async def get_webhook_delivery_stats(db: AsyncSession = Depends(get_db)):
    """Get webhook delivery statistics"""
    try:
        stats = await webhook_delivery_service.get_webhook_delivery_stats(db)
        
        return WebhookDeliveryResponse(
            success=True,
            message="Webhook delivery statistics retrieved successfully",
            data=stats
        )
        
    except Exception as e:
        logger.error(f"Error getting webhook delivery stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get webhook delivery stats: {str(e)}"
        )


@router.post("/retry-failed", response_model=WebhookDeliveryResponse)
async def retry_failed_webhooks(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Manually retry failed webhook deliveries"""
    try:
        # Run retry in background
        background_tasks.add_task(webhook_delivery_service.retry_failed_webhooks, db)
        
        return WebhookDeliveryResponse(
            success=True,
            message="Webhook retry process initiated in background",
            data={"status": "retrying"}
        )
        
    except Exception as e:
        logger.error(f"Error initiating webhook retry: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initiate webhook retry: {str(e)}"
        )


@router.post("/check-critical-events", response_model=WebhookDeliveryResponse)
async def check_critical_event_fallbacks(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Manually check for missing critical events and trigger polling fallback"""
    try:
        # Run check in background
        background_tasks.add_task(webhook_delivery_service.check_critical_event_fallbacks, db)
        
        return WebhookDeliveryResponse(
            success=True,
            message="Critical event fallback check initiated in background",
            data={"status": "checking"}
        )
        
    except Exception as e:
        logger.error(f"Error checking critical event fallbacks: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to check critical event fallbacks: {str(e)}"
        )


@router.post("/proactive-check", response_model=WebhookDeliveryResponse)
async def trigger_proactive_webhook_failure_check(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Manually trigger proactive webhook failure check"""
    try:
        # Run proactive check in background
        background_tasks.add_task(webhook_delivery_service._proactive_webhook_failure_check, db)
        
        return WebhookDeliveryResponse(
            success=True,
            message="Proactive webhook failure check initiated in background",
            data={"status": "checking"}
        )
        
    except Exception as e:
        logger.error(f"Error triggering proactive webhook failure check: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to trigger proactive webhook failure check: {str(e)}"
        )


@router.get("/health", response_model=WebhookDeliveryResponse)
async def get_webhook_delivery_health(db: AsyncSession = Depends(get_db)):
    """Get webhook delivery health status"""
    try:
        stats = await webhook_delivery_service.get_webhook_delivery_stats(db)
        
        # Determine health status
        total_webhooks = stats.get("total_webhooks", 0)
        delivered = stats.get("status_counts", {}).get("delivered", 0)
        failed = stats.get("status_counts", {}).get("failed", 0)
        permanently_failed = stats.get("status_counts", {}).get("permanently_failed", 0)
        
        if total_webhooks == 0:
            health_status = "no_webhooks"
        elif permanently_failed > 0:
            health_status = "critical"
        elif failed > 0:
            health_status = "warning"
        else:
            health_status = "healthy"
        
        health_data = {
            "status": health_status,
            "total_webhooks": total_webhooks,
            "delivered": delivered,
            "failed": failed,
            "permanently_failed": permanently_failed,
            "success_rate": stats.get("delivery_success_rate", 0)
        }
        
        return WebhookDeliveryResponse(
            success=True,
            message="Webhook delivery health status retrieved",
            data=health_data
        )
        
    except Exception as e:
        logger.error(f"Error getting webhook delivery health: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get webhook delivery health: {str(e)}"
        )


@router.post("/configure", response_model=WebhookDeliveryResponse)
async def configure_webhook_delivery(
    max_retry_attempts: Optional[int] = None,
    fallback_timeout: Optional[int] = None
):
    """Configure webhook delivery service parameters"""
    try:
        if max_retry_attempts is not None:
            webhook_delivery_service.max_retry_attempts = max(1, max_retry_attempts)
        
        if fallback_timeout is not None:
            webhook_delivery_service.fallback_timeout = max(60, fallback_timeout)  # Minimum 1 minute
        
        return WebhookDeliveryResponse(
            success=True,
            message="Webhook delivery service configured successfully",
            data={
                "max_retry_attempts": webhook_delivery_service.max_retry_attempts,
                "fallback_timeout": webhook_delivery_service.fallback_timeout
            }
        )
        
    except Exception as e:
        logger.error(f"Error configuring webhook delivery service: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to configure webhook delivery service: {str(e)}"
        )
