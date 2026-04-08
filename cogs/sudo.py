from __future__ import annotations

import logging
import platform
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
        prefix = ctx.prefix or "!"
        cmds = [
            "sudo add <user>", "sudo remove <user>", "sudo list",
            "sudo ban user <user_id>", "sudo ban guild <guild_id>",
            "sudo unban <user>", "sudo leave", "sudo guilds",
            "sudo bot stats/restart/shutdown", "sudo cog load/reload/unload <cog>",
            "sudo customize status/presence <...>", "sudo default",
            "sudo msg <message>", "sudo guild config", "sudo icon [url]",
        ]
        await ctx.send(
            embed=UI.info(
                f"`{Emoji.INFO}` **Sudo Commands**\n\n"
                + "\n".join(f"> `{prefix}{c}`" for c in cmds)
            )
        )

    @sudo.command(name="add")
    @commands.is_owner()
    async def sudo_add(self, ctx: "PushieContext", user: discord.User) -> None:
        """Add a user to sudo list."""
        await self.bot.storage.add_sudo(user.id)
        await ctx.ok(f"*{user.mention} added to sudo users.*")

    @sudo.command(name="list")
    @commands.is_owner()
    async def sudo_list(self, ctx: "PushieContext") -> None:
        """List all sudo users."""
        if not self.bot.storage.global_data.sudo_users:
            await ctx.info("*No sudo users configured.*")
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
        await ctx.ok(f"*{user.mention} removed from sudo users.*")

    # ======== Ban Management ========
    @sudo.group(name="ban", invoke_without_command=True)
    @commands.is_owner()
    async def sudo_ban(self, ctx: "PushieContext") -> None:
        """Ban a user or guild from using the bot."""
        prefix = ctx.prefix or "!"
        await ctx.info(f"*Use: `{prefix}sudo ban user <id>` or `{prefix}sudo ban guild <id>`*")

    @sudo_ban.command(name="user")
    @commands.is_owner()
    async def sudo_ban_user(self, ctx: "PushieContext", user_id: int) -> None:
        """Ban a user ID from using the bot."""
        await self.bot.storage.ban_user(user_id)
        await ctx.ok(f"*User `{user_id}` banned from using the bot.*")

    @sudo_ban.command(name="guild")
    @commands.is_owner()
    async def sudo_ban_guild(self, ctx: "PushieContext", guild_id: int) -> None:
        """Ban a guild ID and leave it."""
        await self.bot.storage.ban_guild(guild_id)
        guild = self.bot.get_guild(guild_id)
        if guild:
            try:
                await guild.leave()
                await ctx.ok(f"*Guild `{guild.name}` banned and left.*")
            except Exception:
                await ctx.ok(f"*Guild `{guild_id}` banned (could not leave).*")
        else:
            await ctx.ok(f"*Guild `{guild_id}` banned.*")

    @sudo.command(name="unban")
    @commands.is_owner()
    async def sudo_unban(self, ctx: "PushieContext", user_id: int) -> None:
        """Unban a user."""
        await self.bot.storage.unban_user(user_id)
        await ctx.ok(f"*User `{user_id}` unbanned.*")

    # ======== Bot Management ========
    @sudo.command(name="leave")
    @commands.is_owner()
    async def sudo_leave(self, ctx: "PushieContext") -> None:
        """Make the bot leave the current guild."""
        if not ctx.guild:
            await ctx.err("*This command only works in a guild.*")
            return
        await ctx.ok("*Leaving...*")
        await ctx.guild.leave()

    @sudo.command(name="guilds")
    @commands.is_owner()
    async def sudo_guilds(self, ctx: "PushieContext") -> None:
        """List all guilds the bot is in."""
        lines = [
            f"> `{i + 1}.` **{g.name}** — {g.member_count} members (ID: `{g.id}`)"
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
            hours, rem = divmod(uptime.seconds, 3600)
            minutes, _ = divmod(rem, 60)
            # Get system stats
            try:
                import psutil
                proc = psutil.Process()
                mem_mb = proc.memory_info().rss / 1024 / 1024
                cpu_p = psutil.cpu_percent(interval=0.1)
                mem_total_mb = psutil.virtual_memory().total / 1024 / 1024
                sys_info = (
                    f"> **CPU** — `{cpu_p:.1f}%`\n"
                    f"> **Memory** — `{mem_mb:.1f} MB` / `{mem_total_mb:.0f} MB`\n"
                )
            except ImportError:
                sys_info = "> *psutil not installed*\n"
            stats_text = (
                f"> `{Emoji.INFO}` **Bot Statistics**\n"
                f"> **Uptime** — `{uptime.days}d {hours}h {minutes}m`\n"
                f"> **Guilds** — `{len(self.bot.guilds)}`\n"
                f"> **Users** — `{len(self.bot.users)}`\n"
                f"> **Cogs** — `{len(self.bot.cogs)}`\n"
                f"> **Commands** — `{len(self.bot.commands)}`\n"
                f"> **Python** — `{platform.python_version()}`\n"
                f"> **discord.py** — `{discord.__version__}`\n"
                + sys_info
            )
            embed = discord.Embed(description=stats_text, color=0xFAB9EC)
            await ctx.send(embed=embed)
        elif action == "restart":
            await ctx.ok("*Restarting bot...*")
            await self.bot.close()
        elif action == "shutdown":
            await ctx.ok("*Shutting down bot...*")
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
                await ctx.ok(f"*Cog `{cog}` loaded.*")
            elif action == "reload":
                await self.bot.reload_extension(f"cogs.{cog}")
                await ctx.ok(f"*Cog `{cog}` reloaded.*")
            elif action == "unload":
                await self.bot.unload_extension(f"cogs.{cog}")
                await ctx.ok(f"*Cog `{cog}` unloaded.*")
        except commands.ExtensionError as e:
            await ctx.err(f"*Error: `{e}`*")

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
        status_map = {
            "dnd": discord.Status.dnd,
            "idle": discord.Status.idle,
            "online": discord.Status.online,
            "invisible": discord.Status.invisible,
        }
        activity_type_map = {
            "watching": discord.ActivityType.watching,
            "listening": discord.ActivityType.listening,
            "streaming": discord.ActivityType.streaming,
            "playing": discord.ActivityType.playing,
            "competing": discord.ActivityType.competing,
        }

        if customize_type == "status" and message:
            key = message.strip().lower()
            status = status_map.get(key)
            if status:
                await self.bot.change_presence(status=status)
                await ctx.ok(f"*Status set to `{key}`.*")
            else:
                await ctx.err(f"*Unknown status. Valid: `{', '.join(status_map)}`*")
        elif customize_type == "presence" and message:
            parts = message.split(" ", 1)
            if len(parts) < 2:
                await ctx.err("*Usage: `sudo customize presence <type> <text>`*")
                return
            act_key, act_text = parts[0].lower(), parts[1]
            atype = activity_type_map.get(act_key)
            if not atype:
                await ctx.err(f"*Unknown type. Valid: `{', '.join(activity_type_map)}`*")
                return
            activity = discord.Activity(type=atype, name=act_text)
            await self.bot.change_presence(activity=activity)
            await ctx.ok(f"*Presence updated: `{act_key} {act_text}`*")
        else:
            await ctx.err("*Provide a type and message.*")

    @sudo.command(name="default")
    @commands.is_owner()
    async def sudo_default(self, ctx: "PushieContext") -> None:
        """Reset presence to default."""
        await self.bot.change_presence(
            activity=discord.Activity(type=discord.ActivityType.listening, name="!help")
        )
        await ctx.ok("*Presence reset to default.*")

    @sudo.command(name="msg")
    @commands.is_owner()
    async def sudo_msg(self, ctx: "PushieContext", *, message: str) -> None:
        """Send a message to the system channel of this guild."""
        if not ctx.guild:
            await ctx.err("*This command only works in a guild.*")
            return
        ch = ctx.guild.system_channel
        if ch and ch.permissions_for(ctx.guild.me).send_messages:
            await ch.send(message)
            await ctx.ok(f"*Message sent to {ch.mention}.*")
        else:
            await ctx.err("*No system channel found or no permission to send.*")

    @sudo.command(name="guild")
    @commands.is_owner()
    async def sudo_guild(self, ctx: "PushieContext", action: Literal["config"]) -> None:
        """Guild configuration inspection."""
        if action == "config":
            if not ctx.guild:
                await ctx.err("*This command only works in a guild.*")
                return
            g = await self.bot.storage.get_guild(ctx.guild.id)
            import json
            config_text = json.dumps(g.to_dict(), indent=2)
            if len(config_text) > 1800:
                config_text = config_text[:1800] + "\n..."
            await ctx.send(f"```json\n{config_text}\n```")

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
                await ctx.err("*Provide a URL or attachment.*")
                return
            await self.bot.user.edit(avatar=data)
            await ctx.ok("*Avatar updated.*")
        except Exception as e:
            await ctx.err(f"*Error: `{e}`*")

    @sudo.command(name="prefix")
    @commands.is_owner()
    async def sudo_prefix(self, ctx: "PushieContext", *, new_prefix: str) -> None:
        """Change the global bot prefix."""
        self.bot.command_prefix = new_prefix  # type: ignore
        await ctx.ok(f"*Global prefix changed to `{new_prefix}`.*")

    @sudo.command(name="blacklist")
    @commands.is_owner()
    async def sudo_blacklist(self, ctx: "PushieContext") -> None:
        """View banned users and guilds."""
        bl_users = self.bot.storage.global_data.banned_users
        bl_guilds = self.bot.storage.global_data.banned_guilds
        lines = []
        if bl_users:
            lines.append(f"> **Users:** {', '.join(f'`{u}`' for u in bl_users[:10])}")
        if bl_guilds:
            lines.append(f"> **Guilds:** {', '.join(f'`{g}`' for g in bl_guilds[:10])}")
        if not lines:
            await ctx.info("*Blacklist is empty.*")
            return
        await ctx.send(embed=UI.info(f"`{Emoji.BLACKLIST}` **Blacklist**\n\n" + "\n".join(lines)))

    async def cog_command_error(self, ctx: commands.Context, error: Exception) -> None:
        if isinstance(error, (commands.CommandInvokeError, commands.HybridCommandError)):
            error = error.original  # type: ignore
        if isinstance(error, commands.NotOwner):
            await ctx.send(embed=UI.error("*This command is restricted to the bot owner.*"))
        elif isinstance(error, commands.CheckFailure):
            await ctx.send(embed=UI.error(str(error)))
        else:
            raise error


async def setup(bot: "Pushie") -> None:
    await bot.add_cog(Sudo(bot))
