from fastapi import APIRouter, HTTPException, Depends, Header
from fastapi.security import HTTPBearer
from typing import Optional
from app.services.auth_service import AuthService
from app.schemas.schemas import (
    UserSignUp, 
    UserSignIn, 
    UserResponse, 
    AuthResponse,
    MessageResponse
)
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()


@router.post("/signup", response_model=AuthResponse)
async def sign_up(user_data: UserSignUp):
    """Sign up a new user"""
    try:
        auth_service = AuthService()
        result = await auth_service.sign_up(
            email=user_data.email,
            password=user_data.password
        )
        
        if result["success"]:
            return AuthResponse(
                success=True,
                message=result["message"],
                user=UserResponse(**result["user"]),
                session=result.get("session")
            )
        else:
            raise HTTPException(status_code=400, detail=result["message"])
            
    except Exception as e:
        logger.error(f"Error in signup endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/signin", response_model=AuthResponse)
async def sign_in(user_data: UserSignIn):
    """Sign in an existing user"""
    try:
        auth_service = AuthService()
        result = await auth_service.sign_in(
            email=user_data.email,
            password=user_data.password
        )
        
        if result["success"]:
            return AuthResponse(
                success=True,
                message=result["message"],
                user=UserResponse(**result["user"]),
                session=result["session"]
            )
        else:
            raise HTTPException(status_code=401, detail=result["message"])
            
    except Exception as e:
        logger.error(f"Error in signin endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/signout", response_model=MessageResponse)
async def sign_out(authorization: Optional[str] = Header(None)):
    """Sign out the current user"""
    try:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid authorization header")
        
        access_token = authorization.replace("Bearer ", "")
        auth_service = AuthService()
        result = await auth_service.sign_out(access_token)
        
        if result["success"]:
            return MessageResponse(message=result["message"])
        else:
            raise HTTPException(status_code=400, detail=result["message"])
            
    except Exception as e:
        logger.error(f"Error in signout endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/me", response_model=UserResponse)
async def get_current_user(authorization: Optional[str] = Header(None)):
    """Get current user information"""
    try:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid authorization header")
        
        access_token = authorization.replace("Bearer ", "")
        auth_service = AuthService()
        
        try:
            user = await auth_service.get_user(access_token)
        except Exception as auth_error:
            logger.error(f"Auth service error: {auth_error}")
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        
        if user:
            try:
                return UserResponse(**user)
            except Exception as validation_error:
                logger.error(f"UserResponse validation error: {validation_error}")
                logger.error(f"User data: {user}")
                raise HTTPException(status_code=500, detail="User data validation failed")
        else:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_current_user endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/refresh", response_model=AuthResponse)
async def refresh_session(refresh_token: str):
    """Refresh the access token"""
    try:
        auth_service = AuthService()
        session = await auth_service.refresh_session(refresh_token)
        
        if session:
            return AuthResponse(
                success=True,
                message="Session refreshed successfully",
                session=session
            )
        else:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
            
    except Exception as e:
        logger.error(f"Error in refresh_session endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(email: str):
    """Send password reset email"""
    try:
        auth_service = AuthService()
        result = await auth_service.reset_password(email)
        
        if result["success"]:
            return MessageResponse(message=result["message"])
        else:
            raise HTTPException(status_code=400, detail=result["message"])
            
    except Exception as e:
        logger.error(f"Error in reset_password endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/profile", response_model=UserResponse)
async def update_profile(
    user_metadata: dict,
    authorization: Optional[str] = Header(None)
):
    """Update user profile"""
    try:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid authorization header")
        
        access_token = authorization.replace("Bearer ", "")
        auth_service = AuthService()
        result = await auth_service.update_user(access_token, user_metadata)
        
        if result["success"]:
            return UserResponse(**result["user"])
        else:
            raise HTTPException(status_code=400, detail=result["message"])
            
    except Exception as e:
        logger.error(f"Error in update_profile endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
