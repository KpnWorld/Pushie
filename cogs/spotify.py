from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import discord
from discord.ext import commands

from emojis import Emoji
from ui import UI

if TYPE_CHECKING:
    from main import Pushie, PushieContext

log = logging.getLogger(__name__)


class Spotify(commands.Cog, name="Spotify"):
    """Spotify integration commands."""

    def __init__(self, bot: "Pushie") -> None:
        self.bot = bot
        self.linked_accounts: dict[int, str] = {}

    @commands.hybrid_group(name="spotify", description="Spotify commands")
    async def spotify(self, ctx: "PushieContext") -> None:
        await ctx.info("Spotify commands: `link`, `now`, `playlist`, `search`")

    @spotify.command(name="link", description="Link your Spotify account")
    async def spotify_link(self, ctx: "PushieContext", username: str) -> None:
        self.linked_accounts[ctx.author.id] = username
        await ctx.ok(f"Linked Spotify account: **{username}**")

    @spotify.command(name="now", description="Show your currently playing track")
    async def spotify_now(self, ctx: "PushieContext") -> None:
        if ctx.author.id not in self.linked_accounts:
            await ctx.err("You haven't linked your Spotify account yet.")
            return

        username = self.linked_accounts[ctx.author.id]
        embed = discord.Embed(
            description=f"> `{Emoji.MUSIC}` *Now playing on **{username}***",
            color=0xFAB9EC,
        )
        embed.set_footer(text="Spotify Integration")
        await ctx.send(embed=embed)

    @spotify.command(name="playlist", description="Create or manage a playlist")
    async def spotify_playlist(
        self, ctx: "PushieContext", action: str, *, name: str
    ) -> None:
        if ctx.author.id not in self.linked_accounts:
            await ctx.err("You haven't linked your Spotify account yet.")
            return

        if action.lower() == "create":
            await ctx.ok(f"Created playlist: **{name}**")
        elif action.lower() == "delete":
            await ctx.ok(f"Deleted playlist: **{name}**")
        else:
            await ctx.err("Action must be `create` or `delete`.")

    @spotify.command(name="search", description="Search Spotify for a track")
    async def spotify_search(self, ctx: "PushieContext", *, query: str) -> None:
        embed = discord.Embed(
            description=f"> `{Emoji.MUSIC}` *Searching Spotify for: **{query}***",
            color=0xFAB9EC,
        )
        embed.set_footer(text="Top results would appear here")
        await ctx.send(embed=embed)

    async def cog_command_error(self, ctx: commands.Context, error: Exception) -> None:
        if isinstance(error, commands.BadArgument):
            await ctx.send(embed=UI.error("*Invalid argument provided.*"))
        else:
            raise error


async def setup(bot: "Pushie") -> None:
    await bot.add_cog(Spotify(bot))
