import asyncio
import threading
import time
import subprocess
import json
import os
from typing import Optional, Dict, Any
import logging
import requests

logger = logging.getLogger(__name__)


class CloudflareTunnelService:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(CloudflareTunnelService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, 'initialized'):
            return
        
        self.initialized = True
        self.tunnel_process = None
        self.public_url = None
        self.webhook_url = None
        self.is_running = False
        self.external_url = None  # For externally managed tunnel
        self.tunnel_name = os.getenv('CLOUDFLARE_TUNNEL_NAME', 'meeting-bot-tunnel')
        self.tunnel_domain = os.getenv('CLOUDFLARE_TUNNEL_DOMAIN')
        self.tunnel_port = int(os.getenv('CLOUDFLARE_TUNNEL_PORT', '8000'))
        
        # Try to detect existing external tunnel
        self._detect_external_tunnel()
    
    def _detect_external_tunnel(self):
        """Detect externally running Cloudflare tunnel"""
        try:
            # Check if tunnel is running by looking for cloudflared process
            result = subprocess.run(['pgrep', '-f', 'cloudflared'], capture_output=True, text=True)
            if result.returncode == 0:
                # Try to get tunnel info from cloudflared
                try:
                    result = subprocess.run(['cloudflared', 'tunnel', 'info', self.tunnel_name], 
                                          capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        # Parse tunnel info to get public URL
                        lines = result.stdout.split('\n')
                        for line in lines:
                            if 'url=' in line:
                                self.external_url = line.split('=')[1].strip()
                                self.public_url = self.external_url
                                self.webhook_url = f"{self.external_url}/webhook/"
                                self.is_running = True
                                
                                logger.info(f"Detected external Cloudflare tunnel: {self.external_url}")
                                logger.info(f"External webhook URL: {self.webhook_url}")
                                return
                except Exception as e:
                    logger.debug(f"Could not get tunnel info: {e}")
                    
        except Exception as e:
            logger.debug(f"Could not detect external Cloudflare tunnel: {e}")
    
    def set_external_url(self, external_url: str):
        """Manually set external Cloudflare tunnel URL"""
        if external_url:
            self.external_url = external_url.rstrip('/')
            self.public_url = self.external_url
            self.webhook_url = f"{self.external_url}/webhook/"
            self.is_running = True
            
            logger.info(f"Set external Cloudflare tunnel URL: {self.external_url}")
            logger.info(f"Webhook URL: {self.webhook_url}")
    
    def start_tunnel(self, port: int = 8000, domain: Optional[str] = None) -> str:
        """Start Cloudflare tunnel"""
        try:
            # If external tunnel is already detected, return that
            if self.external_url:
                logger.info(f"Using existing external Cloudflare tunnel: {self.external_url}")
                return self.external_url
            
            if self.is_running and self.tunnel_process:
                logger.info("Cloudflare tunnel already running")
                return self.public_url
            
            logger.info(f"Starting Cloudflare tunnel on port {port}")
            
            # Build cloudflared command
            cmd = ['cloudflared', 'tunnel', '--url', f'http://localhost:{port}']
            
            # Add custom domain if provided
            if domain:
                cmd.extend(['--hostname', domain])
                logger.info(f"Using custom domain: {domain}")
            
            # Start tunnel process
            self.tunnel_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait a bit for tunnel to start and get URL
            time.sleep(3)
            
            # Try to get the tunnel URL
            try:
                result = subprocess.run(['cloudflared', 'tunnel', 'info', self.tunnel_name], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if 'url=' in line:
                            self.public_url = line.split('=')[1].strip()
                            self.webhook_url = f"{self.public_url}/webhook/"
                            self.is_running = True
                            
                            logger.info(f"Cloudflare tunnel started: {self.public_url}")
                            logger.info(f"Webhook URL: {self.webhook_url}")
                            
                            return self.public_url
            except Exception as e:
                logger.warning(f"Could not get tunnel info: {e}")
            
            # Fallback: use tunnel name to construct URL
            if not self.public_url:
                self.public_url = f"https://{self.tunnel_name}.trycloudflare.com"
                self.webhook_url = f"{self.public_url}/webhook/"
                self.is_running = True
                
                logger.info(f"Cloudflare tunnel started (fallback): {self.public_url}")
                logger.info(f"Webhook URL: {self.webhook_url}")
            
            return self.public_url
            
        except Exception as e:
            logger.error(f"Error starting Cloudflare tunnel: {e}")
            # Try to detect external tunnel as fallback
            self._detect_external_tunnel()
            if self.external_url:
                return self.external_url
            raise
    
    def stop_tunnel(self):
        """Stop Cloudflare tunnel"""
        try:
            if self.external_url:
                logger.info("Cannot stop external Cloudflare tunnel - managed externally")
                return
                
            if self.tunnel_process:
                self.tunnel_process.terminate()
                self.tunnel_process.wait(timeout=5)
                self.tunnel_process = None
                self.public_url = None
                self.webhook_url = None
                self.is_running = False
                logger.info("Cloudflare tunnel stopped")
            else:
                logger.info("No Cloudflare tunnel to stop")
                
        except Exception as e:
            logger.error(f"Error stopping Cloudflare tunnel: {e}")
    
    def get_webhook_url(self) -> Optional[str]:
        """Get the current webhook URL"""
        # Refresh external tunnel detection
        if not self.webhook_url:
            self._detect_external_tunnel()
        return self.webhook_url
    
    def get_public_url(self) -> Optional[str]:
        """Get the current public URL"""
        # Refresh external tunnel detection
        if not self.public_url:
            self._detect_external_tunnel()
        return self.public_url
    
    def get_tunnel_info(self) -> Dict[str, Any]:
        """Get tunnel information"""
        return {
            "is_running": self.is_running,
            "public_url": self.public_url,
            "webhook_url": self.webhook_url,
            "tunnel_name": self.tunnel_name,
            "tunnel_domain": self.tunnel_domain,
            "external_url": self.external_url,
            "managed_externally": bool(self.external_url)
        }
    
    def restart_tunnel(self, port: int = 8000, domain: Optional[str] = None) -> str:
        """Restart Cloudflare tunnel"""
        if self.external_url:
            logger.info("Cannot restart external Cloudflare tunnel - managed externally")
            return self.external_url
            
        logger.info("Restarting Cloudflare tunnel")
        self.stop_tunnel()
        time.sleep(1)  # Give tunnel time to clean up
        return self.start_tunnel(port, domain)
    
    def is_tunnel_active(self) -> bool:
        """Check if tunnel is active"""
        # Refresh external tunnel detection
        if not self.is_running:
            self._detect_external_tunnel()
        return self.is_running
    
    def get_tunnels_info(self) -> list:
        """Get all active tunnels"""
        try:
            # Get tunnels from cloudflared
            result = subprocess.run(['cloudflared', 'tunnel', 'list'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                tunnels = []
                lines = result.stdout.split('\n')[1:]  # Skip header
                for line in lines:
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 4:
                            tunnels.append({
                                "name": parts[0],
                                "id": parts[1],
                                "created": parts[2],
                                "connections": parts[3],
                                "external": False
                            })
                return tunnels
        except Exception as e:
            logger.error(f"Error getting tunnels info: {e}")
        
        return []
    
    def refresh_external_detection(self):
        """Manually refresh external tunnel detection"""
        self._detect_external_tunnel()
        return self.get_tunnel_info()
    
    def __del__(self):
        """Cleanup on destruction"""
        if not self.external_url:  # Only stop if we manage the tunnel
            self.stop_tunnel()


# Global instance
cloudflare_tunnel_service = CloudflareTunnelService()
