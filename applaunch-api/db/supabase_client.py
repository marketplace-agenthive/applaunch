# applaunch-api/db/supabase_client.py
"""Supabase singleton client — import get_supabase() anywhere in the app."""

from functools import lru_cache
from supabase import create_client, Client
from config import get_settings


@lru_cache()
def get_supabase() -> Client:
    """Return a cached Supabase service-role client (one per process)."""
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_key)
