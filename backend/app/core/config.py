from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    # Core Configuration
    app_name: str = Field(default="Meahana Attendee", description="Application name")
    environment: str = Field(default="development", description="Environment")
    debug: bool = Field(default=False, description="Debug mode")
    
    # Database
    database_url: str = Field(..., description="Database connection URL")
    
    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0", description="Redis connection URL")
    
    # Attendee API
    attendee_api_key: str = Field(..., description="Attendee API key")
    attendee_api_base_url: str = Field(default="https://app.attendee.dev", description="Attendee API base URL")
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment.lower() == "production"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings() 