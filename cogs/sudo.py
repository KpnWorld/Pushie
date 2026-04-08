from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING, Literal

import discord
from discord.ext import commands

from emojis import Emoji
from ui import UI

if TYPE_CHECKING:
    from main import Pushie, PushieContext

log = logging.getLogger(__name__)


class Sudo(commands.Cog, name="Sudo"):
    """Bot owner commands for managing sudo access and bot configuration."""

    def __init__(self, bot: "Pushie") -> None:
        self.bot = bot

    # ======== Sudo User Management ========
    @commands.group(name="sudo", aliases=["su"], invoke_without_command=True)
    @commands.is_owner()
    async def sudo(self, ctx: "PushieContext") -> None:
        """Sudo command group."""
        pass

    @sudo.command(name="add")
    @commands.is_owner()
    async def sudo_add(self, ctx: "PushieContext", user: discord.User) -> None:
        """Add a user to sudo list."""
        await self.bot.storage.add_sudo(user.id)
        await ctx.ok(f"Added {user.mention} to sudo users.")

    @sudo.command(name="list")
    @commands.is_owner()
    async def sudo_list(self, ctx: "PushieContext") -> None:
        """List all sudo users."""
        if not self.bot.storage.global_data.sudo_users:
            await ctx.info("No sudo users configured.")
            return

        lines = [
            f"> `{i + 1}.` <@{uid}>"
            for i, uid in enumerate(self.bot.storage.global_data.sudo_users)
        ]
        embed = discord.Embed(
            description=f"`{Emoji.INFO}` **Sudo Users**\n\n" + "\n".join(lines),
            color=0xFAB9EC,
        )
        await ctx.send(embed=embed)

    @sudo.command(name="remove")
    @commands.is_owner()
    async def sudo_remove(self, ctx: "PushieContext", user: discord.User) -> None:
        """Remove a user from sudo list."""
        await self.bot.storage.remove_sudo(user.id)
        await ctx.ok(f"Removed {user.mention} from sudo users.")

    # ======== Ban Management ========
    @sudo.command(name="ban")
    @commands.is_owner()
    async def sudo_ban(
        self,
        ctx: "PushieContext",
        target_type: Literal["user", "guild"],
        target: discord.User | discord.Guild,
    ) -> None:
        """Ban a user or guild from using the bot."""
        if target_type == "user":
            if isinstance(target, discord.User):
                await self.bot.storage.ban_user(target.id)
                await ctx.ok(f"Banned user {target.mention}")
        elif target_type == "guild":
            if isinstance(target, discord.Guild):
                await self.bot.storage.ban_guild(target.id)
                try:
                    await target.leave()
                    await ctx.ok(f"Banned and left guild {target.name}")
                except Exception:
                    await ctx.ok(f"Banned guild {target.name}")

    @sudo.command(name="unban")
    @commands.is_owner()
    async def sudo_unban(self, ctx: "PushieContext", user: discord.User) -> None:
        """Unban a user."""
        await self.bot.storage.unban_user(user.id)
        await ctx.ok(f"Unbanned user {user.mention}")

    # ======== Bot Management ========
    @sudo.command(name="leave")
    @commands.is_owner()
    async def sudo_leave(self, ctx: "PushieContext") -> None:
        """Make the bot leave the current guild."""
        if not ctx.guild:
            await ctx.err("This command only works in a guild.")
            return
        await ctx.ok("Leaving...")
        await ctx.guild.leave()

    @sudo.command(name="guilds")
    @commands.is_owner()
    async def sudo_guilds(self, ctx: "PushieContext") -> None:
        """List all guilds the bot is in."""
        lines = [
            f"> `{i + 1}.` **{g.name}** — {g.member_count} members (ID: {g.id})"
            for i, g in enumerate(self.bot.guilds[:20])
        ]
        extra = (
            f"\n> *+{len(self.bot.guilds) - 20} more...*"
            if len(self.bot.guilds) > 20
            else ""
        )
        embed = discord.Embed(
            description=f"`{Emoji.INFO}` **Guilds ({len(self.bot.guilds)} total)**\n\n"
            + "\n".join(lines)
            + extra,
            color=0xFAB9EC,
        )
        await ctx.send(embed=embed)

    @sudo.command(name="bot")
    @commands.is_owner()
    async def sudo_bot(
        self, ctx: "PushieContext", action: Literal["stats", "restart", "shutdown"]
    ) -> None:
        """Bot internal management."""
        if action == "stats":
            uptime = self.bot.uptime
            stats_text = (
                f"> `{Emoji.INFO}` **Bot Statistics**\n"
                f"> Uptime: `{uptime.days}d {uptime.seconds // 3600}h`\n"
                f"> Guilds: `{len(self.bot.guilds)}`\n"
                f"> Loaded Cogs: `{len(self.bot.cogs)}`"
            )
            embed = discord.Embed(description=stats_text, color=0xFAB9EC)
            await ctx.send(embed=embed)
        elif action == "restart":
            await ctx.ok("Restarting bot...")
            await self.bot.close()
        elif action == "shutdown":
            await ctx.ok("Shutting down bot...")
            await self.bot.close()

    @sudo.command(name="cog")
    @commands.is_owner()
    async def sudo_cog(
        self,
        ctx: "PushieContext",
        action: Literal["load", "reload", "unload"],
        cog: str,
    ) -> None:
        """Manage cogs."""
        try:
            if action == "load":
                await self.bot.load_extension(f"cogs.{cog}")
                await ctx.ok(f"Loaded cog `{cog}`")
            elif action == "reload":
                await self.bot.reload_extension(f"cogs.{cog}")
                await ctx.ok(f"Reloaded cog `{cog}`")
            elif action == "unload":
                await self.bot.unload_extension(f"cogs.{cog}")
                await ctx.ok(f"Unloaded cog `{cog}`")
        except commands.ExtensionError as e:
            await ctx.err(f"Error: {e}")

    @sudo.command(name="customize")
    @commands.is_owner()
    async def sudo_customize(
        self,
        ctx: "PushieContext",
        customize_type: Literal["status", "presence"],
        *,
        message: str | None = None,
    ) -> None:
        """Change bot status or presence."""
        activity_map = {
            "🔴": discord.Status.dnd,
            "🟡": discord.Status.idle,
            "🟢": discord.Status.online,
            "🫥": discord.Status.invisible,
        }
        activity_type_map = {
            "👀": discord.ActivityType.watching,
            "👂": discord.ActivityType.listening,
            "🟣": discord.ActivityType.streaming,
        }

        if customize_type == "status" and message:
            status = activity_map.get(message.strip())
            if status:
                await self.bot.change_presence(status=status)
                await ctx.ok(f"Status changed to `{message.strip()}`")
        elif customize_type == "presence" and message:
            activity_type = activity_type_map.get(message.split()[0])
            if activity_type:
                activity = discord.Activity(
                    type=activity_type, name=" ".join(message.split()[1:])
                )
                await self.bot.change_presence(activity=activity)
                await ctx.ok(f"Presence updated")

    @sudo.command(name="default")
    @commands.is_owner()
    async def sudo_default(self, ctx: "PushieContext") -> None:
        """Save current presence as default."""
        await ctx.ok("*Current presence saved as default.*")

    @sudo.command(name="msg")
    @commands.is_owner()
    async def sudo_msg(self, ctx: "PushieContext", *, message: str) -> None:
        """Send a guild-wide message (max 2 per day)."""
        if not ctx.guild:
            await ctx.err("This command only works in a guild.")
            return

        count = 0
        for channel in ctx.guild.text_channels:
            if channel.permissions_for(ctx.guild.me).send_messages:
                try:
                    await channel.send(message)
                    count += 1
                except discord.Forbidden:
                    pass

        await ctx.ok(f"Message sent to {count} channels.")

    @sudo.command(name="guild")
    @commands.is_owner()
    async def sudo_guild(self, ctx: "PushieContext", action: Literal["config"]) -> None:
        """Guild configuration inspection."""
        if action == "config":
            if not ctx.guild:
                await ctx.err("This command only works in a guild.")
                return
            g = await self.bot.storage.get_guild(ctx.guild.id)
            config_text = f"```json\n{g.to_dict()}\n```"
            if len(config_text) > 2000:
                config_text = config_text[:1900] + "\n...\n```"
            await ctx.send(config_text)

    @sudo.command(name="icon")
    @commands.is_owner()
    async def sudo_icon(self, ctx: "PushieContext", *, url: str | None = None) -> None:
        """Update bot's profile picture."""
        assert self.bot.user is not None
        try:
            if ctx.message.attachments:
                data = await ctx.message.attachments[0].read()
            elif url:
                import aiohttp

                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as resp:
                        data = await resp.read()
            else:
                await ctx.err("Provide a URL or attachment.")
                return

            await self.bot.user.edit(avatar=data)
            await ctx.ok("Avatar updated.")
        except Exception as e:
            await ctx.err(f"Error: {e}")


async def setup(bot: "Pushie") -> None:
    await bot.add_cog(Sudo(bot))
