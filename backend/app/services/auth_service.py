import logging
from typing import Optional, Dict, Any
from supabase import Client
from app.core.database import get_supabase

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self):
        self.supabase: Client = get_supabase()
    
    async def sign_up(self, email: str, password: str, user_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Sign up a new user and automatically sign them in"""
        try:
            # First, sign up the user
            signup_response = self.supabase.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": user_metadata or {}
                }
            })
            
            if signup_response.user:
                # Then automatically sign them in to get a session
                signin_response = self.supabase.auth.sign_in_with_password({
                    "email": email,
                    "password": password
                })
                
                if signin_response.user and signin_response.session:
                    return {
                        "success": True,
                        "user": {
                            "id": signin_response.user.id,
                            "email": signin_response.user.email,
                            "created_at": signin_response.user.created_at
                        },
                        "session": {
                            "access_token": signin_response.session.access_token,
                            "refresh_token": signin_response.session.refresh_token,
                            "expires_at": signin_response.session.expires_at
                        },
                        "message": "User created and signed in successfully"
                    }
                else:
                    return {
                        "success": True,
                        "user": {
                            "id": signup_response.user.id,
                            "email": signup_response.user.email,
                            "created_at": signup_response.user.created_at
                        },
                        "message": "User created successfully. Please sign in."
                    }
            else:
                return {
                    "success": False,
                    "message": "Failed to create user"
                }
                
        except Exception as e:
            logger.error(f"Error in sign_up: {e}")
            return {
                "success": False,
                "message": str(e)
            }
    
    async def sign_in(self, email: str, password: str) -> Dict[str, Any]:
        """Sign in an existing user"""
        try:
            response = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if response.user and response.session:
                return {
                    "success": True,
                    "user": {
                        "id": response.user.id,
                        "email": response.user.email,
                        "created_at": response.user.created_at
                    },
                    "session": {
                        "access_token": response.session.access_token,
                        "refresh_token": response.session.refresh_token,
                        "expires_at": response.session.expires_at
                    },
                    "message": "Signed in successfully"
                }
            else:
                return {
                    "success": False,
                    "message": "Invalid credentials"
                }
                
        except Exception as e:
            logger.error(f"Error in sign_in: {e}")
            return {
                "success": False,
                "message": str(e)
            }
    
    async def sign_out(self, access_token: str) -> Dict[str, Any]:
        """Sign out a user"""
        try:
            # For sign out, we don't need to set a session
            # Just clear the token from our side
            # Supabase will handle the token invalidation on their end
            
            return {
                "success": True,
                "message": "Signed out successfully"
            }
                
        except Exception as e:
            logger.error(f"Error in sign_out: {e}")
            return {
                "success": False,
                "message": str(e)
            }
    
    async def get_user(self, access_token: str) -> Optional[Dict[str, Any]]:
        """Get current user from access token"""
        try:
            # Use the access token directly to get user info
            # Don't try to set a session with None refresh_token
            user = self.supabase.auth.get_user(access_token)
            
            if user.user:
                return {
                    "id": user.user.id,
                    "email": user.user.email,
                    "created_at": user.user.created_at,
                    "user_metadata": user.user.user_metadata
                }
            return None
                
        except Exception as e:
            logger.error(f"Error in get_user: {e}")
            return None
    
    async def refresh_session(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """Refresh the session using refresh token"""
        try:
            response = self.supabase.auth.refresh_session(refresh_token)
            
            if response.session:
                return {
                    "access_token": response.session.access_token,
                    "refresh_token": response.session.refresh_token,
                    "expires_at": response.session.expires_at
                }
            return None
                
        except Exception as e:
            logger.error(f"Error in refresh_session: {e}")
            return None
    
    async def reset_password(self, email: str) -> Dict[str, Any]:
        """Send password reset email"""
        try:
            response = self.supabase.auth.reset_password_email(email)
            
            return {
                "success": True,
                "message": "Password reset email sent"
            }
                
        except Exception as e:
            logger.error(f"Error in reset_password: {e}")
            return {
                "success": False,
                "message": str(e)
            }
    
    async def update_user(self, access_token: str, user_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Update user metadata"""
        try:
            # Set the session for the request
            self.supabase.auth.set_session(access_token, None)
            response = self.supabase.auth.update_user({
                "data": user_metadata
            })
            
            if response.user:
                return {
                    "success": True,
                    "user": {
                        "id": response.user.id,
                        "email": response.user.email,
                        "user_metadata": response.user.user_metadata
                    },
                    "message": "User updated successfully"
                }
            else:
                return {
                    "success": False,
                    "message": "Failed to update user"
                }
                
        except Exception as e:
            logger.error(f"Error in update_user: {e}")
            return {
                "success": False,
                "message": str(e)
            }
