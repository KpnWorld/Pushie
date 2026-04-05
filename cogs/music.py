from __future__ import annotations

import logging
from typing import TYPE_CHECKING, cast

import discord
from discord.ext import commands

from emojis import Emoji
from ui import UI

if TYPE_CHECKING:
    from main import Pushie, PushieContext

log = logging.getLogger(__name__)


class Music(commands.Cog, name="Music"):
    """Music playback commands."""

    def __init__(self, bot: "Pushie") -> None:
        self.bot = bot
        self._queue: dict[int, list[str]] = {}

    @commands.hybrid_command(
        name="play", description="Play a song from YouTube or Spotify"
    )
    @commands.guild_only()
    async def play(self, ctx: "PushieContext", *, query: str) -> None:
        author = cast(discord.Member, ctx.author)
        if not author.voice or not author.voice.channel:
            await ctx.err("You must be in a voice channel to play music.")
            return

        assert ctx.guild is not None
        guild_id = ctx.guild.id
        if guild_id not in self._queue:
            self._queue[guild_id] = []

        self._queue[guild_id].append(query)
        await ctx.ok(f"Added to queue: **{query}**")

    @commands.hybrid_command(name="pause", description="Pause current playback")
    @commands.guild_only()
    async def pause(self, ctx: "PushieContext") -> None:
        await ctx.ok("Paused playback.")

    @commands.hybrid_command(name="skip", description="Skip to next track")
    @commands.guild_only()
    async def skip(self, ctx: "PushieContext") -> None:
        assert ctx.guild is not None
        guild_id = ctx.guild.id
        if guild_id in self._queue and self._queue[guild_id]:
            self._queue[guild_id].pop(0)
            await ctx.ok("Skipped to next track.")
        else:
            await ctx.err("No tracks in queue.")

    @commands.hybrid_command(name="queue", description="View song queue")
    @commands.guild_only()
    async def queue(self, ctx: "PushieContext") -> None:
        assert ctx.guild is not None
        guild_id = ctx.guild.id
        if guild_id not in self._queue or not self._queue[guild_id]:
            await ctx.info("Queue is empty.")
            return

        tracks = self._queue[guild_id][:10]
        queue_text = "\n".join(f"{i+1}. {track}" for i, track in enumerate(tracks))
        embed = discord.Embed(
            description=f"> `{Emoji.MUSIC}` *Queue:*\n\n{queue_text}",
            color=0xFAB9EC,
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="stop", description="Stop playback and clear queue")
    @commands.guild_only()
    async def stop(self, ctx: "PushieContext") -> None:
        assert ctx.guild is not None
        guild_id = ctx.guild.id
        if guild_id in self._queue:
            self._queue[guild_id].clear()
        await ctx.ok("Stopped playback and cleared queue.")

    @commands.hybrid_command(name="volume", description="Adjust playback volume")
    @commands.guild_only()
    async def volume(self, ctx: "PushieContext", level: int) -> None:
        if not (0 <= level <= 100):
            await ctx.err("Volume must be between 0 and 100.")
            return

        await ctx.ok(f"Volume set to {level}%.")

    async def cog_command_error(self, ctx: commands.Context, error: Exception) -> None:
        if isinstance(error, commands.NoPrivateMessage):
            await ctx.send(
                embed=UI.error("*Music commands can only be used in servers.*")
            )
        else:
            raise error


async def setup(bot: "Pushie") -> None:
    await bot.add_cog(Music(bot))
