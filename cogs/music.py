from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING, cast

import discord
import wavelink
from discord.ext import commands

from emojis import Emoji
from ui import UI

if TYPE_CHECKING:
    from main import Pushie, PushieContext

log = logging.getLogger(__name__)


class Music(commands.Cog, name="Music"):
    """Music playback commands with Lavalink."""

    def __init__(self, bot: "Pushie") -> None:
        self.bot = bot
        self.lavalink_host = os.getenv("LAVALINK_HOST", "localhost")
        self.lavalink_port = int(os.getenv("LAVALINK_PORT", "2333"))
        self.lavalink_password = os.getenv("LAVALINK_PASSWORD", "youshallnotpass")

    async def cog_load(self) -> None:
        """Initialize Lavalink connection on cog load."""
        try:
            # Create Lavalink node
            node: wavelink.Node = wavelink.Node(
                uri=f"http://{self.lavalink_host}:{self.lavalink_port}",
                password=self.lavalink_password,
            )
            await wavelink.Pool.connect(nodes=[node], client=self.bot)
            log.info("Connected to Lavalink server")
        except Exception as e:
            log.warning(f"Lavalink not available: {e}")

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node: wavelink.Node) -> None:
        """Called when Lavalink node is ready."""
        log.info(f"Wavelink node {node.identifier} ready")

    @commands.hybrid_command(
        name="play", description="Play a song from YouTube or Spotify"
    )
    @commands.guild_only()
    async def play(self, ctx: "PushieContext", *, query: str) -> None:
        """Play a song by searching YouTube, Spotify, or direct URL."""
        author = cast(discord.Member, ctx.author)
        if not author.voice or not author.voice.channel:
            await ctx.err("*You must be in a voice channel to play music.*")
            return

        assert ctx.guild is not None

        try:
            # Get or create player
            player = cast(wavelink.Player, ctx.guild.voice_client)
            if player is None:
                player = await author.voice.channel.connect(cls=wavelink.Player)
            elif player.channel != author.voice.channel:
                await ctx.err("*I'm already playing in a different channel.*")
                return

            # Search for the track
            async with ctx.typing():
                tracks = await wavelink.Playable.search(query)

            if not tracks:
                await ctx.err(f"*No tracks found matching: {query}*")
                return

            track = tracks[0]
            await player.queue.put_wait(track)

            embed = discord.Embed(
                title=f"`{Emoji.MUSIC}` Added to Queue",
                color=0xFAB9EC,
                description=f"**{track.title}** by {track.author}",
            )
            embed.add_field(
                name="Duration",
                value=f"`{track.length // 60000}:{track.length % 60000 // 1000:02d}`",
            )
            embed.add_field(name="Position in Queue", value=f"`{player.queue.count}`")

            # Start playing if not already playing
            if not player.playing:
                await player.play(player.queue.get())

            await ctx.send(embed=embed)

        except Exception as e:
            log.error(f"Play error: {e}")
            await ctx.err(f"*Error playing track: {e}*")

    @commands.hybrid_command(name="pause", description="Pause current playback")
    @commands.guild_only()
    async def pause(self, ctx: "PushieContext") -> None:
        """Pause the currently playing track."""
        assert ctx.guild is not None
        player = cast(wavelink.Player, ctx.guild.voice_client)

        if not player or not player.playing:
            await ctx.err("*Nothing is currently playing.*")
            return

        await player.pause(not player.paused)
        status = "Paused" if player.paused else "Resumed"
        await ctx.ok(f"`{Emoji.MUSIC}` *{status} playback.*")

    @commands.hybrid_command(name="skip", description="Skip to next track")
    @commands.guild_only()
    async def skip(self, ctx: "PushieContext") -> None:
        """Skip the current track and play the next one."""
        assert ctx.guild is not None
        player = cast(wavelink.Player, ctx.guild.voice_client)

        if not player or not player.playing:
            await ctx.err("*Nothing is currently playing.*")
            return

        try:
            await player.skip(force=True)
            await ctx.ok(f"`{Emoji.MUSIC}` *Skipped to next track.*")
        except Exception as e:
            await ctx.err(f"*Error skipping: {e}*")

    @commands.hybrid_command(name="queue", description="View song queue")
    @commands.guild_only()
    async def queue(self, ctx: "PushieContext") -> None:
        """View the current song queue."""
        assert ctx.guild is not None
        player = cast(wavelink.Player, ctx.guild.voice_client)

        if not player or player.queue.is_empty:
            await ctx.info("*Queue is empty.*")
            return

        # Show current track + next 9
        tracks = [player.current] if player.current else []
        tracks.extend(list(player.queue)[:9])

        queue_text = ""
        for i, track in enumerate(tracks):
            duration = f"{track.length // 60000}:{track.length % 60000 // 1000:02d}"
            indicator = "▶️" if i == 0 else f"{i}."
            queue_text += (
                f"{indicator} **{track.title}** by {track.author} [`{duration}`]\n"
            )

        embed = discord.Embed(
            title=f"`{Emoji.MUSIC}` Queue ({len(tracks)} tracks)",
            description=queue_text,
            color=0xFAB9EC,
        )
        embed.set_footer(
            text=f"Total queue size: {player.queue.count + (1 if player.current else 0)}"
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="stop", description="Stop playback and clear queue")
    @commands.guild_only()
    async def stop(self, ctx: "PushieContext") -> None:
        """Stop playback and disconnect from voice channel."""
        assert ctx.guild is not None
        player = cast(wavelink.Player, ctx.guild.voice_client)

        if not player:
            await ctx.err("*I'm not connected to a voice channel.*")
            return

        try:
            player.queue.clear()
            await player.stop()
            await player.disconnect()
            await ctx.ok(f"`{Emoji.MUSIC}` *Stopped playback and disconnected.*")
        except Exception as e:
            await ctx.err(f"*Error stopping playback: {e}*")

    @commands.hybrid_command(name="volume", description="Adjust playback volume")
    @commands.guild_only()
    async def volume(self, ctx: "PushieContext", level: int) -> None:
        """Adjust the playback volume (0-100)."""
        if not (0 <= level <= 100):
            await ctx.err("*Volume must be between 0 and 100.*")
            return

        assert ctx.guild is not None
        player = cast(wavelink.Player, ctx.guild.voice_client)

        if not player:
            await ctx.err("*I'm not connected to a voice channel.*")
            return

        await player.set_volume(level)
        await ctx.ok(f"`{Emoji.MUSIC}` *Volume set to {level}%.*")

    @commands.hybrid_command(name="nowplaying", description="Show current track info")
    @commands.guild_only()
    async def nowplaying(self, ctx: "PushieContext") -> None:
        """Show information about the currently playing track."""
        assert ctx.guild is not None
        player = cast(wavelink.Player, ctx.guild.voice_client)

        if not player or not player.current:
            await ctx.err("*Nothing is currently playing.*")
            return

        track = player.current
        duration = f"{track.length // 60000}:{track.length % 60000 // 1000:02d}"
        position = f"{player.position // 60000}:{player.position % 60000 // 1000:02d}"

        embed = discord.Embed(
            title=f"`{Emoji.MUSIC}` Now Playing",
            description=f"**{track.title}**",
            color=0xFAB9EC,
        )
        embed.add_field(name="Artist", value=track.author, inline=True)
        embed.add_field(name="Duration", value=duration, inline=True)
        embed.add_field(name="Position", value=f"{position} / {duration}", inline=False)
        embed.add_field(name="Source", value=track.source or "Unknown")
        embed.set_footer(text=f"Volume: {player.volume}%")
        await ctx.send(embed=embed)

    async def cog_command_error(self, ctx: commands.Context, error: Exception) -> None:
        if isinstance(error, commands.NoPrivateMessage):
            await ctx.send(
                embed=UI.error("*Music commands can only be used in servers.*")
            )
        else:
            raise error


async def setup(bot: "Pushie") -> None:
    await bot.add_cog(Music(bot))
