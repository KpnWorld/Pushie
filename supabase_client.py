from __future__ import annotations

import os
from supabase import AsyncClient, acreate_client

_client: AsyncClient | None = None


async def get_client() -> AsyncClient:
    """Get or create the Supabase AsyncClient."""
    global _client
    if _client is None:
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            raise ValueError(
                "SUPABASE_URL and SUPABASE_KEY must be set in environment variables"
            )
        
        _client = await acreate_client(supabase_url, supabase_key)
    return _client


async def close_client() -> None:
    """Close the Supabase client."""
    global _client
    if _client is not None:
        # Supabase client cleanup if needed
        _client = None
