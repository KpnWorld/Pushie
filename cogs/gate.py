from __future__ import annotations

import logging
import uuid
from typing import TYPE_CHECKING

import discord
from discord.ext import commands

from emojis import Emoji
from ui import UI, EmbedBuilderModal, substitute, build_ctx_vars

if TYPE_CHECKING:
    from main import Pushie, PushieContext

log = logging.getLogger(__name__)


class Gate(commands.Cog, name="Gate"):
    """Welcome, leave, and ping on join."""

    def __init__(self, bot: "Pushie") -> None:
        self.bot = bot

    # ======== Greet System ========
    @commands.group(name="greet", invoke_without_command=True)
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def greet(self, ctx: "PushieContext") -> None:
        """Greet system management."""
        pass

    @greet.command(name="setup")
    async def greet_setup(self, ctx: "PushieContext", toggle: str) -> None:
        """Enable or disable greet system."""
        if toggle.lower() not in ["enable", "disable"]:
            await ctx.err("Use `enable` or `disable`")
            return

        assert ctx.guild is not None
        enabled = toggle.lower() == "enable"
        await self.bot.storage.update_setup(ctx.guild.id, greet_enabled=enabled)
        status = (
            f"`{Emoji.SUCCESS}` enabled" if enabled else f"`{Emoji.CANCEL}` disabled"
        )
        await ctx.ok(f"Greet system {status}")

    @greet.command(name="channel")
    async def greet_channel(
        self, ctx: "PushieContext", channel: discord.TextChannel
    ) -> None:
        """Set greet channel."""
        assert ctx.guild is not None
        await self.bot.storage.update_setup(ctx.guild.id, greet_channel=channel.id)
        await ctx.ok(f"Greet channel set to {channel.mention}")

    @greet.command(name="message")
    async def greet_message(
        self, ctx: "PushieContext", *, message: str | None = None
    ) -> None:
        """Set greet message (opens modal)."""
        assert ctx.guild is not None
        if message and message.lower().startswith("$em"):
            # Inline embed flag
            msg = message[4:].strip()
            await self.bot.storage.update_setup(ctx.guild.id, greet_msg=msg)
            await ctx.ok("Greet message updated")

    @greet.command(name="view")
    async def greet_view(self, ctx: "PushieContext") -> None:
        """View current greet message script."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        if not g.greet_msg:
            await ctx.info("No greet message set")
            return
        await ctx.send(embed=UI.info(g.greet_msg))

    @greet.command(name="clear")
    async def greet_clear(self, ctx: "PushieContext") -> None:
        """Clear greet system."""
        assert ctx.guild is not None
        await self.bot.storage.update_setup(
            ctx.guild.id,
            greet_enabled=False,
            greet_channel=None,
            greet_msg=None,
        )
        await ctx.ok("Greet system cleared")

    @greet.command(name="test")
    async def greet_test(self, ctx: "PushieContext") -> None:
        """Test greet output."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        if not g.greet_msg or not g.greet_channel:
            await ctx.err("Greet system not configured")
            return

        member = ctx.author if isinstance(ctx.author, discord.Member) else None
        vars = build_ctx_vars(ctx.guild, member)
        msg = substitute(g.greet_msg, vars)
        await ctx.send(msg)

    # ======== Leave System ========
    @commands.group(name="leave", invoke_without_command=True)
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def leave(self, ctx: "PushieContext") -> None:
        """Leave message system."""
        pass

    @leave.command(name="setup")
    async def leave_setup(self, ctx: "PushieContext", toggle: str) -> None:
        """Enable or disable leave system."""
        if toggle.lower() not in ["enable", "disable"]:
            await ctx.err("Use `enable` or `disable`")
            return

        assert ctx.guild is not None
        enabled = toggle.lower() == "enable"
        await self.bot.storage.update_setup(ctx.guild.id, leave_enabled=enabled)
        status = (
            f"`{Emoji.SUCCESS}` enabled" if enabled else f"`{Emoji.CANCEL}` disabled"
        )
        await ctx.ok(f"Leave system {status}")

    @leave.command(name="channel")
    async def leave_channel(
        self, ctx: "PushieContext", channel: discord.TextChannel
    ) -> None:
        """Set leave channel."""
        assert ctx.guild is not None
        await self.bot.storage.update_setup(ctx.guild.id, leave_channel=channel.id)
        await ctx.ok(f"Leave channel set to {channel.mention}")

    @leave.command(name="message")
    async def leave_message(
        self, ctx: "PushieContext", *, message: str | None = None
    ) -> None:
        """Set leave message."""
        assert ctx.guild is not None
        if message:
            await self.bot.storage.update_setup(ctx.guild.id, leave_msg=message)
            await ctx.ok("Leave message updated")

    @leave.command(name="view")
    async def leave_view(self, ctx: "PushieContext") -> None:
        """View leave message."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        if not g.leave_msg:
            await ctx.info("No leave message set")
            return
        await ctx.send(embed=UI.info(g.leave_msg))

    @leave.command(name="clear")
    async def leave_clear(self, ctx: "PushieContext") -> None:
        """Clear leave system."""
        assert ctx.guild is not None
        await self.bot.storage.update_setup(
            ctx.guild.id,
            leave_enabled=False,
            leave_channel=None,
            leave_msg=None,
        )
        await ctx.ok("Leave system cleared")

    @leave.command(name="test")
    async def leave_test(self, ctx: "PushieContext") -> None:
        """Test leave output."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        if not g.leave_msg or not g.leave_channel:
            await ctx.err("Leave system not configured")
            return

        member = ctx.author if isinstance(ctx.author, discord.Member) else None
        vars = build_ctx_vars(ctx.guild, member)
        msg = substitute(g.leave_msg, vars)
        await ctx.send(msg)

    # ======== Ping on Join ========
    @commands.group(name="pingonjoin", invoke_without_command=True)
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def pingonjoin(self, ctx: "PushieContext") -> None:
        """Ping roles when members join."""
        pass

    @pingonjoin.command(name="setup")
    async def ping_setup(self, ctx: "PushieContext", toggle: str) -> None:
        """Enable or disable ping on join."""
        if toggle.lower() not in ["enable", "disable"]:
            await ctx.err("Use `enable` or `disable`")
            return

        assert ctx.guild is not None
        enabled = toggle.lower() == "enable"
        await self.bot.storage.update_setup(ctx.guild.id, ping_enabled=enabled)
        status = (
            f"`{Emoji.SUCCESS}` enabled" if enabled else f"`{Emoji.CANCEL}` disabled"
        )
        await ctx.ok(f"Ping on join {status}")

    @pingonjoin.command(name="add")
    async def ping_add(
        self, ctx: "PushieContext", channel: discord.TextChannel, autodelete: int = 3
    ) -> None:
        """Add ping assignment."""
        assert ctx.guild is not None
        await self.bot.storage.add_ping_assignment(
            ctx.guild.id,
            channel.id,
            {"autodelete": autodelete},
        )
        await ctx.ok(f"Ping assigned to {channel.mention}")

    @pingonjoin.command(name="remove")
    async def ping_remove(
        self, ctx: "PushieContext", channel: discord.TextChannel
    ) -> None:
        """Remove ping assignment."""
        assert ctx.guild is not None
        await self.bot.storage.remove_ping_assignment(ctx.guild.id, channel.id)
        await ctx.ok(f"Removed ping from {channel.mention}")

    @pingonjoin.command(name="list")
    async def ping_list(self, ctx: "PushieContext") -> None:
        """List ping assignments."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        if not g.ping_assignments:
            await ctx.info("No ping assignments")
            return

        lines = [
            f"> `{i + 1}.` <#{cid}>" for i, cid in enumerate(g.ping_assignments.keys())
        ]
        embed = discord.Embed(
            description=f"`{Emoji.INFO}` **Ping Assignments**\n\n" + "\n".join(lines),
            color=0xFAB9EC,
        )
        await ctx.send(embed=embed)


async def setup(bot: "Pushie") -> None:
    await bot.add_cog(Gate(bot))
