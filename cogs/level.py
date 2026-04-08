from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import discord
from discord.ext import commands

from emojis import Emoji

if TYPE_CHECKING:
    from main import Pushie, PushieContext

log = logging.getLogger(__name__)


class Level(commands.Cog, name="Levels"):
    """Leveling and XP system."""

    def __init__(self, bot: "Pushie") -> None:
        self.bot = bot

    @commands.group(name="levels", invoke_without_command=True)
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def levels(self, ctx: "PushieContext") -> None:
        """Leveling system."""
        pass

    @levels.command(name="setup")
    async def levels_setup(self, ctx: "PushieContext", toggle: str) -> None:
        """Enable or disable level system."""
        if toggle.lower() not in ["enable", "disable"]:
            await ctx.err("Use `enable` or `disable`")
            return

        assert ctx.guild is not None
        enabled = toggle.lower() == "enable"
        await self.bot.storage.update_setup(ctx.guild.id, levels_enabled=enabled)
        status = (
            f"`{Emoji.SUCCESS}` enabled" if enabled else f"`{Emoji.CANCEL}` disabled"
        )
        await ctx.ok(f"Level system {status}")

    @levels.command(name="channel")
    async def levels_channel(
        self, ctx: "PushieContext", channel: discord.TextChannel
    ) -> None:
        """Set level-up channel."""
        assert ctx.guild is not None
        await self.bot.storage.update_setup(ctx.guild.id, levels_channel=channel.id)
        await ctx.ok(f"Level channel set to {channel.mention}")

    @levels.command(name="message")
    async def levels_message(self, ctx: "PushieContext", *, message: str) -> None:
        """Set level-up message template."""
        assert ctx.guild is not None
        await self.bot.storage.update_setup(ctx.guild.id, levels_msg=message)
        await ctx.ok("Level message updated")

    @levels.command(name="msg")
    async def levels_msg(self, ctx: "PushieContext", *, message: str) -> None:
        """Update level-up message."""
        assert ctx.guild is not None
        await self.bot.storage.update_setup(ctx.guild.id, levels_msg=message)
        await ctx.ok("Level message updated")

    @levels.command(name="reset")
    async def levels_reset(self, ctx: "PushieContext") -> None:
        """Reset all XP data."""
        assert ctx.guild is not None
        await self.bot.storage.update_setup(ctx.guild.id, levels_xp_leaderboard={})
        await ctx.ok("Level data reset")

    @levels.command(name="leaderboard")
    async def levels_leaderboard(self, ctx: "PushieContext") -> None:
        """Show top users by XP."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        if not g.levels_xp_leaderboard:
            await ctx.info("No level data yet")
            return

        sorted_users = sorted(
            g.levels_xp_leaderboard.items(), key=lambda x: x[1], reverse=True
        )[:7]

        lines = [
            f"> `{i + 1}.` <@{uid}> — `{xp} XP`"
            for i, (uid, xp) in enumerate(sorted_users)
        ]

        embed = discord.Embed(
            description=f"`{Emoji.INFO}` **Top Levelers**\n\n" + "\n".join(lines),
            color=0xFAB9EC,
        )
        await ctx.send(embed=embed)

    @levels.command(name="add")
    async def levels_add(
        self, ctx: "PushieContext", level: int, role: discord.Role
    ) -> None:
        """Add level with associated role."""
        assert ctx.guild is not None
        await self.bot.storage.add_level(ctx.guild.id, level, role.id)
        await ctx.ok(f"Level `{level}` → {role.mention}")

    @levels.command(name="remove")
    async def levels_remove(self, ctx: "PushieContext", level: int) -> None:
        """Remove level."""
        assert ctx.guild is not None
        await self.bot.storage.remove_level(ctx.guild.id, level)
        await ctx.ok(f"Removed level `{level}`")

    @levels.command(name="list")
    async def levels_list(self, ctx: "PushieContext") -> None:
        """List all configured levels."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        if not g.levels_list:
            await ctx.info("No levels configured")
            return

        lines = [
            f"> `Level {l['level']}` → <@&{l['role_id']}>"
            for l in sorted(g.levels_list, key=lambda x: x["level"])
        ]

        embed = discord.Embed(
            description=f"`{Emoji.INFO}` **Levels**\n\n" + "\n".join(lines),
            color=0xFAB9EC,
        )
        await ctx.send(embed=embed)


async def setup(bot: "Pushie") -> None:
    await bot.add_cog(Level(bot))
