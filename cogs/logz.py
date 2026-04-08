from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Literal

import discord
from discord.ext import commands

from emojis import Emoji
from ui import UI

if TYPE_CHECKING:
    from main import Pushie, PushieContext

log = logging.getLogger(__name__)


class Logz(commands.Cog, name="Logz"):
    """Logging system for server events."""

    def __init__(self, bot: "Pushie") -> None:
        self.bot = bot

    @commands.group(name="logz", aliases=["lg"], invoke_without_command=True)
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def logz(self, ctx: "PushieContext") -> None:
        """Logging system management."""
        pass

    @logz.command(name="add")
    async def logz_add(
        self,
        ctx: "PushieContext",
        event_type: Literal["member", "mod", "role", "channel", "voice"],
        channel: discord.TextChannel,
    ) -> None:
        """Add log assignment for an event type."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)

        event_key = f"{event_type}_channel"
        await self.bot.storage.update_setup(ctx.guild.id, **{event_key: channel.id})

        if event_type not in g.log_events:
            g.log_events.append(event_type)
            await self.bot.storage.save_guild(g)

        await ctx.ok(f"Logs for `{event_type}` events → {channel.mention}")

    @logz.command(name="remove")
    async def logz_remove(
        self,
        ctx: "PushieContext",
        event_type: Literal["member", "mod", "role", "channel", "voice"],
    ) -> None:
        """Remove log assignment."""
        assert ctx.guild is not None
        event_key = f"{event_type}_channel"
        await self.bot.storage.update_setup(ctx.guild.id, **{event_key: None})

        g = await self.bot.storage.get_guild(ctx.guild.id)
        if event_type in g.log_events:
            g.log_events.remove(event_type)
            await self.bot.storage.save_guild(g)

        await ctx.ok(f"Removed logs for `{event_type}`")

    @logz.command(name="view")
    async def logz_view(self, ctx: "PushieContext") -> None:
        """View all log assignments."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)

        lines = []
        for event in g.log_events:
            event_key = f"{event}_channel"
            channel_id = getattr(g, event_key, None)
            if channel_id:
                lines.append(f"> `{event}` — <#{channel_id}>")

        if not lines:
            await ctx.info("No logs configured")
            return

        embed = discord.Embed(
            description=f"`{Emoji.INFO}` **Log Assignments**\n\n" + "\n".join(lines),
            color=0xFAB9EC,
        )
        await ctx.send(embed=embed)

    @logz.command(name="color")
    async def logz_color(self, ctx: "PushieContext", hex_color: str) -> None:
        """Set color of log embeds."""
        assert ctx.guild is not None
        try:
            color = int(hex_color.lstrip("#"), 16)
            await self.bot.storage.update_setup(ctx.guild.id, log_color=color)
            await ctx.ok(f"Log color set to `{hex_color}`")
        except ValueError:
            await ctx.err("Invalid hex color")

    @logz.command(name="test")
    async def logz_test(
        self,
        ctx: "PushieContext",
        event_type: Literal["member", "mod", "role", "channel", "voice"],
    ) -> None:
        """Test log output."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        event_key = f"{event_type}_channel"
        channel_id = getattr(g, event_key, None)

        if not channel_id:
            await ctx.err(f"No channel configured for `{event_type}` logs")
            return

        channel = ctx.guild.get_channel(channel_id)
        if not channel or not isinstance(channel, discord.TextChannel):
            await ctx.err("Log channel not found or is not a text channel")
            return

        test_embed = discord.Embed(
            title=f"Test {event_type.capitalize()} Log",
            description=f"This is a test log entry for {event_type} events",
            color=g.log_color,
        ).set_footer(text=f"Logged at")

        try:
            await channel.send(embed=test_embed)
            await ctx.ok(f"Test log sent to {channel.mention}")
        except discord.Forbidden:
            await ctx.err(f"Cannot send messages to {channel.mention}")


async def setup(bot: "Pushie") -> None:
    await bot.add_cog(Logz(bot))
