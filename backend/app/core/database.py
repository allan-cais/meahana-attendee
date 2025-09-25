from supabase import create_client, Client
from app.core.config import settings
from typing import Generator

# Create Supabase client
supabase: Client = create_client(
    settings.supabase_url,
    settings.supabase_service_role_key
)

# Dependency to get Supabase client
def get_supabase() -> Client:
    return supabase 