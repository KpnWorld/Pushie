from __future__ import annotations

import logging
import random
from typing import TYPE_CHECKING

import discord
from discord.ext import commands

from emojis import Emoji
from ui import UI, substitute, build_ctx_vars

if TYPE_CHECKING:
    from main import Pushie, PushieContext

log = logging.getLogger(__name__)


class Level(commands.Cog, name="Levels"):
    """Leveling and XP system."""

    def __init__(self, bot: "Pushie") -> None:
        self.bot = bot
        self._xp_cooldown: dict[int, float] = {}

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return
        if not message.guild:
            return

        g = self.bot.storage.get_guild_sync(message.guild.id)
        if not g or not g.levels_enabled:
            return

        user_id = message.author.id
        import time
        now = time.time()
        last = self._xp_cooldown.get(user_id, 0)
        if now - last < 60:
            return
        self._xp_cooldown[user_id] = now

        xp_gain = random.randint(15, 25)
        old_xp = self.bot.storage.get_user_xp(g, user_id)
        old_level = self.bot.storage.xp_to_level(old_xp)

        await self.bot.storage.add_xp(message.guild.id, user_id, xp_gain)

        g = await self.bot.storage.get_guild(message.guild.id)
        new_xp = self.bot.storage.get_user_xp(g, user_id)
        new_level = self.bot.storage.xp_to_level(new_xp)

        if new_level > old_level:
            await self._on_level_up(message, new_level, g)

    async def _on_level_up(self, message: discord.Message, new_level: int, g: object) -> None:
        assert message.guild is not None
        member = message.author
        if not isinstance(member, discord.Member):
            return

        # Assign level roles
        from storage import GuildData
        if isinstance(g, GuildData):
            for entry in g.levels_list:
                if entry.get("level") == new_level:
                    role = message.guild.get_role(entry["role_id"])
                    if role and role not in member.roles:
                        try:
                            await member.add_roles(role, reason=f"Level {new_level} reached")
                        except (discord.Forbidden, discord.HTTPException):
                            pass

            # Send level-up message
            level_msg = g.levels_msg or f"🎉 {member.mention} reached **Level {new_level}**!"
            vars = build_ctx_vars(message.guild, member)
            vars["level"] = str(new_level)
            content = substitute(level_msg, vars)

            target_channel = None
            if g.levels_channel:
                target_channel = message.guild.get_channel(g.levels_channel)

            if isinstance(target_channel, discord.TextChannel):
                try:
                    await target_channel.send(content)
                except (discord.Forbidden, discord.HTTPException):
                    pass
            elif isinstance(message.channel, discord.TextChannel):
                try:
                    await message.channel.send(content, delete_after=10)
                except (discord.Forbidden, discord.HTTPException):
                    pass

    @commands.group(name="levels", invoke_without_command=True)
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def levels(self, ctx: "PushieContext") -> None:
        """Leveling system management."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        enabled = f"`{Emoji.SUCCESS}` enabled" if g.levels_enabled else f"`{Emoji.CANCEL}` disabled"
        ch = f"<#{g.levels_channel}>" if g.levels_channel else "*not set*"
        prefix = ctx.prefix or "!"
        await ctx.send(
            embed=UI.info(
                f"`{Emoji.STATS}` **Level System** — {enabled}\n"
                f"> **Channel:** {ch}\n\n"
                f"```\n{prefix}levels setup enable/disable\n"
                f"{prefix}levels channel <channel>\n"
                f"{prefix}levels message <channel> <msg>\n"
                f"{prefix}levels msg <message>\n"
                f"{prefix}levels leaderboard\n"
                f"{prefix}levels add <level> <role>\n"
                f"{prefix}levels remove <level>\n"
                f"{prefix}levels list\n"
                f"{prefix}levels reset\n```"
            )
        )

    @levels.command(name="setup")
    async def levels_setup(self, ctx: "PushieContext", toggle: str) -> None:
        """Enable or disable level system."""
        if toggle.lower() not in ["enable", "disable"]:
            await ctx.err("Use `enable` or `disable`")
            return
        assert ctx.guild is not None
        enabled = toggle.lower() == "enable"
        await self.bot.storage.update_setup(ctx.guild.id, levels_enabled=enabled)
        status = f"`{Emoji.SUCCESS}` enabled" if enabled else f"`{Emoji.CANCEL}` disabled"
        await ctx.ok(f"Level system {status}")

    @levels.command(name="channel")
    async def levels_channel(self, ctx: "PushieContext", channel: discord.TextChannel) -> None:
        """Set level-up notification channel."""
        assert ctx.guild is not None
        await self.bot.storage.update_setup(ctx.guild.id, levels_channel=channel.id)
        await ctx.ok(f"Level-up channel set to {channel.mention}")

    @levels.command(name="message")
    async def levels_message(self, ctx: "PushieContext", channel: discord.TextChannel | None = None, *, message: str = "") -> None:
        """Set level-up channel and message."""
        assert ctx.guild is not None
        update: dict = {}
        if channel:
            update["levels_channel"] = channel.id
        if message:
            update["levels_msg"] = message
        if update:
            await self.bot.storage.update_setup(ctx.guild.id, **update)
        await ctx.ok("Level message" + (f" and channel set to {channel.mention}" if channel else " updated"))

    @levels.command(name="msg")
    async def levels_msg(self, ctx: "PushieContext", *, message: str) -> None:
        """Update level-up message template. Use $user.mention, $guild.name, $level."""
        assert ctx.guild is not None
        await self.bot.storage.update_setup(ctx.guild.id, levels_msg=message)
        await ctx.ok("Level-up message updated")

    @levels.command(name="reset")
    async def levels_reset(self, ctx: "PushieContext") -> None:
        """Reset all XP data for this server."""
        assert ctx.guild is not None
        await self.bot.storage.update_setup(ctx.guild.id, levels_xp_leaderboard={})
        await ctx.ok("All level data has been reset")

    @levels.command(name="leaderboard")
    async def levels_leaderboard(self, ctx: "PushieContext") -> None:
        """Show top 7 users by XP."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        if not g.levels_xp_leaderboard:
            await ctx.info("No level data yet")
            return

        sorted_users = sorted(
            g.levels_xp_leaderboard.items(), key=lambda x: x[1], reverse=True
        )[:7]

        lines = []
        for i, (uid, xp) in enumerate(sorted_users):
            level = self.bot.storage.xp_to_level(int(xp))
            lines.append(f"> `{i + 1}.` <@{uid}> — Level `{level}` (`{xp} XP`)")

        embed = discord.Embed(
            description=f"`{Emoji.STATS}` **Level Leaderboard**\n\n" + "\n".join(lines),
            color=0xFAB9EC,
        )
        await ctx.send(embed=embed)

    @levels.command(name="add")
    async def levels_add(self, ctx: "PushieContext", level: int, role: discord.Role) -> None:
        """Add a role reward for reaching a level."""
        assert ctx.guild is not None
        await self.bot.storage.add_level(ctx.guild.id, level, role.id)
        await ctx.ok(f"Level `{level}` → {role.mention}")

    @levels.command(name="remove")
    async def levels_remove(self, ctx: "PushieContext", level: int) -> None:
        """Remove a level role reward."""
        assert ctx.guild is not None
        await self.bot.storage.remove_level(ctx.guild.id, level)
        await ctx.ok(f"Removed level `{level}`")

    @levels.command(name="list")
    async def levels_list(self, ctx: "PushieContext") -> None:
        """List all configured level roles."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        if not g.levels_list:
            await ctx.info("No level roles configured")
            return
        lines = [
            f"> `Level {l['level']}` → <@&{l['role_id']}>"
            for l in sorted(g.levels_list, key=lambda x: x["level"])
        ]
        embed = discord.Embed(
            description=f"`{Emoji.ROLE}` **Level Roles**\n\n" + "\n".join(lines),
            color=0xFAB9EC,
        )
        await ctx.send(embed=embed)


async def setup(bot: "Pushie") -> None:
    await bot.add_cog(Level(bot))
