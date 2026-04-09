from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import discord
from discord.ext import commands

from emojis import Emoji
from ui import UI, substitute, build_ctx_vars

if TYPE_CHECKING:
    from main import Pushie, PushieContext

log = logging.getLogger(__name__)


class Gate(commands.Cog, name="Gate"):
    """Welcome, leave, and ping on join."""

    def __init__(self, bot: "Pushie") -> None:
        self.bot = bot

    # ======== Events ========
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        guild = member.guild
        g = self.bot.storage.get_guild_sync(guild.id)
        if not g:
            return

        # Autoroles
        roles_to_add: list[discord.Role] = []
        for rid in g.autoroles:
            r = guild.get_role(rid)
            if r:
                roles_to_add.append(r)
        if member.bot:
            for rid in g.autoroles_bot:
                r = guild.get_role(rid)
                if r:
                    roles_to_add.append(r)
        else:
            for rid in g.autoroles_human:
                r = guild.get_role(rid)
                if r:
                    roles_to_add.append(r)
        if roles_to_add:
            try:
                await member.add_roles(*roles_to_add, reason="Autorole on join")
            except (discord.Forbidden, discord.HTTPException):
                pass

        # Greet
        if g.greet_enabled and g.greet_channel and g.greet_msg:
            ch = guild.get_channel(g.greet_channel)
            if ch and isinstance(ch, discord.TextChannel):
                vars = build_ctx_vars(guild, member)
                msg = substitute(g.greet_msg, vars)
                try:
                    await ch.send(msg)
                except (discord.Forbidden, discord.HTTPException):
                    pass

        # Ping on join
        if g.ping_enabled and g.ping_assignments:
            for channel_id_str, cfg in g.ping_assignments.items():
                ch = guild.get_channel(int(channel_id_str))
                if ch and isinstance(ch, discord.TextChannel):
                    autodelete = cfg.get("autodelete", 3)
                    try:
                        await ch.send(
                            member.mention,
                            delete_after=float(autodelete),
                        )
                    except (discord.Forbidden, discord.HTTPException):
                        pass

        # Forced nick check
        key = str(member.id)
        if key in g.forced_nicks:
            try:
                await member.edit(nick=g.forced_nicks[key], reason="Forced nick re-applied")
            except (discord.Forbidden, discord.HTTPException):
                pass

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member) -> None:
        guild = member.guild
        g = self.bot.storage.get_guild_sync(guild.id)
        if not g:
            return

        if g.leave_enabled and g.leave_channel and g.leave_msg:
            ch = guild.get_channel(g.leave_channel)
            if ch and isinstance(ch, discord.TextChannel):
                vars = build_ctx_vars(guild, member)
                msg = substitute(g.leave_msg, vars)
                try:
                    await ch.send(msg)
                except (discord.Forbidden, discord.HTTPException):
                    pass

    # ======== Greet System ========
    @commands.group(name="greet", invoke_without_command=True)
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def greet(self, ctx: "PushieContext") -> None:
        """Greet system management."""
        prefix = ctx.prefix or "!"
        await ctx.send(
            embed=UI.info(
                f"`{Emoji.WELCOME}` **Greet System**\n\n"
                f"```\n{prefix}greet setup enable/disable\n"
                f"{prefix}greet config <channel> <message>\n"
                f"{prefix}greet channel <channel>\n"
                f"{prefix}greet message <message>\n"
                f"{prefix}greet view\n"
                f"{prefix}greet clear\n"
                f"{prefix}greet test\n```"
            )
        )

    @greet.command(name="setup")
    async def greet_setup(self, ctx: "PushieContext", toggle: str) -> None:
        """Enable or disable greet system."""
        if toggle.lower() not in ["enable", "disable"]:
            await ctx.err("Use `enable` or `disable`")
            return
        assert ctx.guild is not None
        enabled = toggle.lower() == "enable"
        await self.bot.storage.update_setup(ctx.guild.id, greet_enabled=enabled)
        status = f"`{Emoji.SUCCESS}` enabled" if enabled else f"`{Emoji.CANCEL}` disabled"
        await ctx.ok(f"Greet system {status}")

    @greet.command(name="config")
    async def greet_config(self, ctx: "PushieContext", channel: discord.TextChannel, *, message: str) -> None:
        """One-shot greet setup: set channel and message at once."""
        assert ctx.guild is not None
        await self.bot.storage.set_greet_config(ctx.guild.id, channel.id, message)
        await ctx.ok(f"Greet system configured — channel: {channel.mention}")

    @greet.command(name="channel")
    async def greet_channel(self, ctx: "PushieContext", channel: discord.TextChannel) -> None:
        """Set greet channel."""
        assert ctx.guild is not None
        await self.bot.storage.update_setup(ctx.guild.id, greet_channel=channel.id)
        await ctx.ok(f"Greet channel set to {channel.mention}")

    @greet.command(name="message")
    async def greet_message(self, ctx: "PushieContext", *, message: str) -> None:
        """Set greet message."""
        assert ctx.guild is not None
        await self.bot.storage.update_setup(ctx.guild.id, greet_msg=message)
        await ctx.ok("Greet message updated")

    @greet.command(name="view")
    async def greet_view(self, ctx: "PushieContext") -> None:
        """View current greet message script."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        if not g.greet_msg:
            await ctx.info("No greet message set")
            return
        ch_mention = f"<#{g.greet_channel}>" if g.greet_channel else "*not set*"
        enabled = f"`{Emoji.SUCCESS}` enabled" if g.greet_enabled else f"`{Emoji.CANCEL}` disabled"
        await ctx.send(
            embed=UI.info(
                f"**Greet System** — {enabled}\n"
                f"> **Channel:** {ch_mention}\n"
                f"> **Message:**\n```\n{g.greet_msg[:500]}\n```"
            )
        )

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
        if not g.greet_msg:
            await ctx.err("No greet message set. Use `greet message <text>` first.")
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
        prefix = ctx.prefix or "!"
        await ctx.send(
            embed=UI.info(
                f"`{Emoji.LEAVE}` **Leave System**\n\n"
                f"```\n{prefix}leave setup enable/disable\n"
                f"{prefix}leave config <channel> <message>\n"
                f"{prefix}leave channel <channel>\n"
                f"{prefix}leave message <message>\n"
                f"{prefix}leave view\n"
                f"{prefix}leave clear\n"
                f"{prefix}leave test\n```"
            )
        )

    @leave.command(name="setup")
    async def leave_setup(self, ctx: "PushieContext", toggle: str) -> None:
        """Enable or disable leave system."""
        if toggle.lower() not in ["enable", "disable"]:
            await ctx.err("Use `enable` or `disable`")
            return
        assert ctx.guild is not None
        enabled = toggle.lower() == "enable"
        await self.bot.storage.update_setup(ctx.guild.id, leave_enabled=enabled)
        status = f"`{Emoji.SUCCESS}` enabled" if enabled else f"`{Emoji.CANCEL}` disabled"
        await ctx.ok(f"Leave system {status}")

    @leave.command(name="config")
    async def leave_config(self, ctx: "PushieContext", channel: discord.TextChannel, *, message: str) -> None:
        """One-shot leave setup: set channel and message at once."""
        assert ctx.guild is not None
        await self.bot.storage.set_leave_config(ctx.guild.id, channel.id, message)
        await ctx.ok(f"Leave system configured — channel: {channel.mention}")

    @leave.command(name="channel")
    async def leave_channel(self, ctx: "PushieContext", channel: discord.TextChannel) -> None:
        """Set leave channel."""
        assert ctx.guild is not None
        await self.bot.storage.update_setup(ctx.guild.id, leave_channel=channel.id)
        await ctx.ok(f"Leave channel set to {channel.mention}")

    @leave.command(name="message")
    async def leave_message(self, ctx: "PushieContext", *, message: str) -> None:
        """Set leave message."""
        assert ctx.guild is not None
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
        ch_mention = f"<#{g.leave_channel}>" if g.leave_channel else "*not set*"
        enabled = f"`{Emoji.SUCCESS}` enabled" if g.leave_enabled else f"`{Emoji.CANCEL}` disabled"
        await ctx.send(
            embed=UI.info(
                f"**Leave System** — {enabled}\n"
                f"> **Channel:** {ch_mention}\n"
                f"> **Message:**\n```\n{g.leave_msg[:500]}\n```"
            )
        )

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
        if not g.leave_msg:
            await ctx.err("No leave message set.")
            return
        member = ctx.author if isinstance(ctx.author, discord.Member) else None
        vars = build_ctx_vars(ctx.guild, member)
        msg = substitute(g.leave_msg, vars)
        await ctx.send(msg)

    # ======== Ping on Join ========
    @commands.group(name="pingonjoin", aliases=["poj"], invoke_without_command=True)
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def pingonjoin(self, ctx: "PushieContext") -> None:
        """Ping roles/users when members join."""
        prefix = ctx.prefix or "!"
        await ctx.send(
            embed=UI.info(
                f"`{Emoji.JOIN}` **Ping on Join**\n\n"
                f"```\n{prefix}pingonjoin setup enable/disable\n"
                f"{prefix}pingonjoin add <channel>\n"
                f"{prefix}pingonjoin remove <channel>\n"
                f"{prefix}pingonjoin list\n```"
            )
        )

    @pingonjoin.command(name="setup")
    async def ping_setup(self, ctx: "PushieContext", toggle: str) -> None:
        """Enable or disable ping on join."""
        if toggle.lower() not in ["enable", "disable"]:
            await ctx.err("Use `enable` or `disable`")
            return
        assert ctx.guild is not None
        enabled = toggle.lower() == "enable"
        await self.bot.storage.update_setup(ctx.guild.id, ping_enabled=enabled)
        status = f"`{Emoji.SUCCESS}` enabled" if enabled else f"`{Emoji.CANCEL}` disabled"
        await ctx.ok(f"Ping on join {status}")

    @pingonjoin.command(name="add")
    async def ping_add(self, ctx: "PushieContext", channel: discord.TextChannel, autodelete: int = 3) -> None:
        """Add ping assignment to a channel."""
        assert ctx.guild is not None
        await self.bot.storage.add_ping_assignment(
            ctx.guild.id,
            channel.id,
            {"autodelete": autodelete},
        )
        await ctx.ok(f"Ping assigned to {channel.mention} (autodelete: `{autodelete}s`)")

    @pingonjoin.command(name="remove")
    async def ping_remove(self, ctx: "PushieContext", channel: discord.TextChannel) -> None:
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
            await ctx.info("No ping assignments configured")
            return
        lines = [
            f"> `{i + 1}.` <#{cid}> — autodelete `{cfg.get('autodelete', 3)}s`"
            for i, (cid, cfg) in enumerate(g.ping_assignments.items())
        ]
        embed = discord.Embed(
            description=f"`{Emoji.INFO}` **Ping Assignments**\n\n" + "\n".join(lines),
            color=0xFAB9EC,
        )
        await ctx.send(embed=embed)


async def setup(bot: "Pushie") -> None:
    await bot.add_cog(Gate(bot))
