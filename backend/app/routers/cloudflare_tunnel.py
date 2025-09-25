from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.services.cloudflare_tunnel_service import cloudflare_tunnel_service
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cloudflare-tunnel", tags=["cloudflare-tunnel"])


@router.get("/status")
async def get_tunnel_status():
    """Get Cloudflare tunnel status and information"""
    try:
        tunnel_info = cloudflare_tunnel_service.get_tunnel_info()
        return {
            "status": "success",
            "tunnel_info": tunnel_info
        }
    except Exception as e:
        logger.error(f"Error getting tunnel status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get tunnel status: {str(e)}")


@router.post("/start")
async def start_tunnel(background_tasks: BackgroundTasks):
    """Start Cloudflare tunnel"""
    try:
        if cloudflare_tunnel_service.is_running:
            return {
                "status": "success",
                "message": "Tunnel already running",
                "tunnel_info": cloudflare_tunnel_service.get_tunnel_info()
            }
        
        # Start tunnel in background
        def start_tunnel_task():
            try:
                cloudflare_tunnel_service.start_tunnel(
                    port=settings.cloudflare_tunnel_port,
                    domain=settings.cloudflare_tunnel_domain
                )
            except Exception as e:
                logger.error(f"Background tunnel start failed: {e}")
        
        background_tasks.add_task(start_tunnel_task)
        
        return {
            "status": "success",
            "message": "Starting Cloudflare tunnel...",
            "tunnel_info": cloudflare_tunnel_service.get_tunnel_info()
        }
        
    except Exception as e:
        logger.error(f"Error starting tunnel: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start tunnel: {str(e)}")


@router.post("/stop")
async def stop_tunnel():
    """Stop Cloudflare tunnel"""
    try:
        if not cloudflare_tunnel_service.is_running:
            return {
                "status": "success",
                "message": "Tunnel not running",
                "tunnel_info": cloudflare_tunnel_service.get_tunnel_info()
            }
        
        cloudflare_tunnel_service.stop_tunnel()
        
        return {
            "status": "success",
            "message": "Tunnel stopped",
            "tunnel_info": cloudflare_tunnel_service.get_tunnel_info()
        }
        
    except Exception as e:
        logger.error(f"Error stopping tunnel: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop tunnel: {str(e)}")


@router.post("/restart")
async def restart_tunnel(background_tasks: BackgroundTasks):
    """Restart Cloudflare tunnel"""
    try:
        # Restart tunnel in background
        def restart_tunnel_task():
            try:
                cloudflare_tunnel_service.restart_tunnel(
                    port=settings.cloudflare_tunnel_port,
                    domain=settings.cloudflare_tunnel_domain
                )
            except Exception as e:
                logger.error(f"Background tunnel restart failed: {e}")
        
        background_tasks.add_task(restart_tunnel_task)
        
        return {
            "status": "success",
            "message": "Restarting Cloudflare tunnel...",
            "tunnel_info": cloudflare_tunnel_service.get_tunnel_info()
        }
        
    except Exception as e:
        logger.error(f"Error restarting tunnel: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to restart tunnel: {str(e)}")


@router.post("/set-external-url")
async def set_external_url(url: str):
    """Set external Cloudflare tunnel URL"""
    try:
        if not url:
            raise HTTPException(status_code=400, detail="URL is required")
        
        cloudflare_tunnel_service.set_external_url(url)
        
        return {
            "status": "success",
            "message": f"External tunnel URL set to: {url}",
            "tunnel_info": cloudflare_tunnel_service.get_tunnel_info()
        }
        
    except Exception as e:
        logger.error(f"Error setting external URL: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to set external URL: {str(e)}")


@router.get("/tunnels")
async def list_tunnels():
    """List all Cloudflare tunnels"""
    try:
        tunnels = cloudflare_tunnel_service.get_tunnels_info()
        return {
            "status": "success",
            "tunnels": tunnels
        }
    except Exception as e:
        logger.error(f"Error listing tunnels: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list tunnels: {str(e)}")


@router.get("/webhook-url")
async def get_webhook_url():
    """Get the current webhook URL"""
    try:
        webhook_url = cloudflare_tunnel_service.get_webhook_url()
        return {
            "status": "success",
            "webhook_url": webhook_url
        }
    except Exception as e:
        logger.error(f"Error getting webhook URL: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get webhook URL: {str(e)}")


@router.post("/refresh")
async def refresh_tunnel_detection():
    """Manually refresh external tunnel detection"""
    try:
        tunnel_info = cloudflare_tunnel_service.refresh_external_detection()
        return {
            "status": "success",
            "message": "Tunnel detection refreshed",
            "tunnel_info": tunnel_info
        }
    except Exception as e:
        logger.error(f"Error refreshing tunnel detection: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to refresh tunnel detection: {str(e)}")
