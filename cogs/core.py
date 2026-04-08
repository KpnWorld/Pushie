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


class Core(commands.Cog, name="Core"):
    """Core bot commands: prefix, AFK, and help."""

    def __init__(self, bot: "Pushie") -> None:
        self.bot = bot

    # ======================== PREFIX ========================
    @commands.group(name="prefix", aliases=["px"], invoke_without_command=True)
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def prefix(self, ctx: "PushieContext") -> None:
        """Show or change the bot prefix for this server."""
        assert ctx.guild is not None
        g = self.bot.storage.get_guild_sync(ctx.guild.id)
        current_prefix = g.prefix if g else "!"
        await ctx.send(embed=UI.info(f"Current prefix: `{current_prefix}`"))

    @prefix.command(name="set")
    async def prefix_set(self, ctx: "PushieContext", *, new_prefix: str) -> None:
        """Change server prefix."""
        assert ctx.guild is not None
        if len(new_prefix) > 10:
            await ctx.err("*Prefix must be 10 characters or less.*")
            return
        await self.bot.storage.set_prefix(ctx.guild.id, new_prefix)
        await ctx.ok(f"Prefix changed to: `{new_prefix}`")

    @prefix.command(name="default")
    async def prefix_default(self, ctx: "PushieContext") -> None:
        """Reset to default prefix (!)."""
        assert ctx.guild is not None
        await self.bot.storage.set_prefix(ctx.guild.id, "!")
        await ctx.ok("Prefix reset to default: `!`")

    # ======================== AFK ========================
    @commands.group(name="afk", aliases=["a"], invoke_without_command=True)
    async def afk(self, ctx: "PushieContext") -> None:
        """Activate AFK status (set reason with subcommand)."""
        assert ctx.guild is not None
        since = discord.utils.utcnow().timestamp()
        await self.bot.storage.set_afk(ctx.guild.id, ctx.author.id, "AFK", since)
        await ctx.send(embed=UI.afk(f"{ctx.author.mention} is now AFK"))

    @afk.command(name="set")
    async def afk_set(self, ctx: "PushieContext", *, reason: str) -> None:
        """Set custom AFK reason."""
        assert ctx.guild is not None
        since = discord.utils.utcnow().timestamp()
        await self.bot.storage.set_afk(ctx.guild.id, ctx.author.id, reason, since)
        await ctx.send(embed=UI.afk(f"{ctx.author.mention} is now AFK — *{reason}*"))

    @afk.command(name="msg")
    async def afk_msg(self, ctx: "PushieContext", *, msg: str) -> None:
        """Set custom AFK embed message."""
        assert ctx.guild is not None
        since = discord.utils.utcnow().timestamp()
        await self.bot.storage.set_afk(ctx.guild.id, ctx.author.id, msg, since)
        await ctx.ok("AFK message updated")

    @afk.command(name="default")
    async def afk_default(self, ctx: "PushieContext") -> None:
        """Revert to default AFK embed."""
        assert ctx.guild is not None
        await self.bot.storage.clear_afk(ctx.guild.id, ctx.author.id)
        await ctx.ok("AFK cleared")

    # ======================== HELP ========================
    @commands.group(name="help", aliases=["h"], invoke_without_command=True)
    async def help(
        self, ctx: "PushieContext", *, command_or_module: str | None = None
    ) -> None:
        """Show main help overview or help for specific command/module."""
        if command_or_module is None:
            # Main help overview
            prefix = ctx.prefix or "!"
            await ctx.send(
                embed=UI.info(
                    f"`{Emoji.INFO}` **Help Overview**\n\n"
                    f"> **Command Examples:**\n"
                    f"```\n{prefix}help list — List all modules\n"
                    f"{prefix}help <module> — Help for module (e.g., 'role', 'ticket')\n"
                    f"{prefix}help <command> — Help for specific command\n"
                    f"{prefix}help variables — Embed substitution variables\n```\n"
                    f"> **Quick Start:**\n"
                    f"```\n{prefix}prefix — Show current prefix\n"
                    f"{prefix}afk — Mark as AFK\n{prefix}config — Server settings\n```"
                )
            )
        elif command_or_module.lower() == "list":
            # List all modules
            cogs = [cog.qualified_name for cog in self.bot.cogs.values()]
            cog_list = "\n".join(f"> `{c}`" for c in sorted(cogs)[:20])
            extra = f"\n> *+{len(cogs) - 20} more...*" if len(cogs) > 20 else ""
            await ctx.send(
                embed=discord.Embed(
                    description=f"`{Emoji.INFO}` **Available Modules**\n\n{cog_list}{extra}",
                    color=0xFAB9EC,
                )
            )
        elif command_or_module.lower() == "variables":
            # List embed variables
            await ctx.send(
                embed=UI.info(
                    f"`{Emoji.INFO}` **Embed Substitution Variables**\n\n"
                    f"> **User Variables:**\n"
                    f"```\n$user.name — User's discord.py name\n"
                    f"$user.id — User ID\n"
                    f"$user.mention — @user mention\n```\n"
                    f"> **Server Variables:**\n"
                    f"```\n$guild.name — Server name\n"
                    f"$guild.id — Server ID\n"
                    f"$guild.members — Member count\n```"
                )
            )
        else:
            # Help for specific command or module
            await ctx.info(f"Help for `{command_or_module}` not yet implemented.")

    @help.command(name="list")
    async def help_list(self, ctx: "PushieContext") -> None:
        """List all command modules."""
        cogs = [cog.qualified_name for cog in self.bot.cogs.values()]
        cog_list = "\n".join(f"> `{c}`" for c in sorted(cogs)[:20])
        extra = f"\n> *+{len(cogs) - 20} more...*" if len(cogs) > 20 else ""
        await ctx.send(
            embed=discord.Embed(
                description=f"`{Emoji.INFO}` **Available Modules**\n\n{cog_list}{extra}",
                color=0xFAB9EC,
            )
        )

    @help.command(name="variables")
    async def help_variables(self, ctx: "PushieContext") -> None:
        """List embed substitution variables."""
        await ctx.send(
            embed=UI.info(
                f"`{Emoji.INFO}` **Embed Substitution Variables**\n\n"
                f"> **User Variables:**\n"
                f"```\n$user.name — User's discord.py name\n"
                f"$user.id — User ID\n"
                f"$user.mention — @user mention\n```\n"
                f"> **Server Variables:**\n"
                f"```\n$guild.name — Server name\n"
                f"$guild.id — Server ID\n"
                f"$guild.members — Member count\n```"
            )
        )


async def setup(bot: "Pushie") -> None:
    await bot.add_cog(Core(bot))
