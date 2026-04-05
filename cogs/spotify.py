from __future__ import annotations

import base64
import json
import logging
import os
from typing import TYPE_CHECKING, Any

import aiohttp
import discord
from discord.ext import commands

from emojis import Emoji
from ui import UI

if TYPE_CHECKING:
    from main import Pushie, PushieContext

log = logging.getLogger(__name__)

SPOTIFY_API_BASE = "https://api.spotify.com/v1"
SPOTIFY_AUTH_URL = "https://accounts.spotify.com/api/token"


class Spotify(commands.Cog, name="Spotify"):
    """Spotify integration commands."""

    def __init__(self, bot: "Pushie") -> None:
        self.bot = bot
        self.client_id = os.getenv("SPOTIFY_CLIENT_ID")
        self.client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
        self.access_token: str | None = None
        self.token_expiry: int = 0
        self.user_tokens: dict[int, str] = {}  # user_id -> refresh_token

    async def get_access_token(self) -> str | None:
        """Get a valid Spotify API access token using Client Credentials flow."""
        if not self.client_id or not self.client_secret:
            log.error("Spotify credentials not configured")
            return None

        auth_str = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()

        headers = {"Authorization": f"Basic {auth_str}"}
        data = {"grant_type": "client_credentials"}

        try:
            async with self.bot.session.post(
                SPOTIFY_AUTH_URL, headers=headers, data=data
            ) as resp:
                if resp.status == 200:
                    json_data = await resp.json()
                    self.access_token = json_data["access_token"]
                    self.token_expiry = json_data["expires_in"]
                    return self.access_token
        except Exception as e:
            log.error(f"Spotify auth error: {e}")
        return None

    async def spotify_request(self, endpoint: str) -> dict[str, Any] | None:
        """Make an authenticated request to Spotify API."""
        if not self.access_token:
            await self.get_access_token()

        if not self.access_token:
            return None

        headers = {"Authorization": f"Bearer {self.access_token}"}
        try:
            async with self.bot.session.get(
                f"{SPOTIFY_API_BASE}{endpoint}", headers=headers
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                elif resp.status == 401:
                    # Token expired, refresh
                    await self.get_access_token()
                    return await self.spotify_request(endpoint)
        except Exception as e:
            log.error(f"Spotify API error: {e}")
        return None

    @commands.hybrid_group(name="spotify", description="Spotify commands")
    async def spotify(self, ctx: "PushieContext") -> None:
        """Spotify integration commands."""
        if ctx.invoked_subcommand is None:
            await ctx.info(
                "Spotify commands: `/spotify search`, `/spotify now`, `/spotify link`"
            )

    @spotify.command(name="search", description="Search Spotify for a track")
    async def spotify_search(self, ctx: "PushieContext", *, query: str) -> None:
        """Search Spotify for a track by name or artist."""
        if not self.client_id:
            await ctx.err("*Spotify integration not configured.*")
            return

        async with ctx.typing():
            data = await self.spotify_request(f"/search?q={query}&type=track&limit=5")

        if not data or "tracks" not in data:
            await ctx.err(f"*No results found for: {query}*")
            return

        tracks = data.get("tracks", {}).get("items", [])
        if not tracks:
            await ctx.err(f"*No results found for: {query}*")
            return

        embed = discord.Embed(
            title=f"`{Emoji.MUSIC}` Search Results: {query}",
            color=0x1DB954,
            description="Top 5 results from Spotify:",
        )

        for i, track in enumerate(tracks[:5], 1):
            artists = ", ".join([a["name"] for a in track.get("artists", [])])
            album = track.get("album", {}).get("name", "Unknown")
            duration = f"{track['duration_ms'] // 60000}:{track['duration_ms'] % 60000 // 1000:02d}"

            embed.add_field(
                name=f"**{i}. {track['name']}**",
                value=f"> Artist: {artists}\n> Album: {album}\n> Duration: {duration}",
                inline=False,
            )

        embed.set_footer(text="Use /spotify add <number> to add to queue")
        await ctx.send(embed=embed)

    @spotify.command(name="now", description="Show currently playing on Spotify")
    async def spotify_now(self, ctx: "PushieContext") -> None:
        """Show the track currently playing on user's Spotify (requires link)."""
        if ctx.author.id not in self.user_tokens:
            await ctx.err("*Link your Spotify account first with `/spotify link`*")
            return

        # Note: Requires user token with appropriate scopes
        # This is a placeholder - actual implementation needs user OAuth flow
        embed = discord.Embed(
            title=f"`{Emoji.MUSIC}` Now Playing",
            color=0x1DB954,
            description="*(OAuth flow required to show actual now playing)*",
        )
        await ctx.send(embed=embed)

    @spotify.command(name="link", description="Link your Spotify account")
    async def spotify_link(self, ctx: "PushieContext") -> None:
        """Link your Spotify account (requires OAuth setup)."""
        if not self.client_id:
            await ctx.err("*Spotify integration not configured.*")
            return

        # This requires a more complex OAuth flow with a callback URL
        # For now, provide instructions
        embed = discord.Embed(
            title="`❌` Spotify Account Linking",
            color=0x1DB954,
            description="To enable Spotify account linking, configure OAuth redirect URI in bot settings.",
        )
        embed.add_field(
            name="Required Setup",
            value=(
                "1. Go to https://developer.spotify.com/dashboard\n"
                "2. Create an app and get Client ID/Secret\n"
                "3. Set Redirect URI to your bot's callback endpoint\n"
                "4. Add credentials to `.env`"
            ),
            inline=False,
        )
        await ctx.send(embed=embed)

    async def cog_command_error(self, ctx: commands.Context, error: Exception) -> None:
        if isinstance(error, commands.BadArgument):
            await ctx.send(embed=UI.error("*Invalid argument provided.*"))
        else:
            raise error


async def setup(bot: "Pushie") -> None:
    await bot.add_cog(Spotify(bot))
