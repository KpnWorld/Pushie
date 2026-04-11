from __future__ import annotations

import os
from supabase import AsyncClient, acreate_client

# ── GLOBAL CLIENT ──────────────────────────────────────────────────────────
_client: AsyncClient | None = None


async def get_client() -> AsyncClient:
    """Get or create the Supabase AsyncClient.

    Creates a new client on first call using SUPABASE_URL and SUPABASE_KEY
    environment variables. Returned client is cached for reuse.

    Returns:
        AsyncClient: The Supabase async client instance.

    Raises:
        ValueError: If SUPABASE_URL or SUPABASE_KEY env vars are missing.
    """
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
    """Close the Supabase client and clear the global reference."""
    global _client
    if _client is not None:
        _client = None
