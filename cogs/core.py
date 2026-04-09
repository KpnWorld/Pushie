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

_MODULE_HELP: dict[str, str] = {
    "core": "prefix, afk, ping, help",
    "gate": "greet, leave, pingonjoin",
    "levels": "levels setup/channel/msg/leaderboard/add/remove/list/reset",
    "logz": "logz add/remove/view/color/test",
    "moderation": "kick/ban/unban/mute/jail/warn/purge/lock/snipe/timeout/lockdown/invoke",
    "roles": "role/channel/server/user/ticket/reactionrole/buttonrole/autorole/boosterrole/friendgroup/config",
    "miscellaneous": "embed/color/timer/counter/reminder",
    "security": "filter/antinuke/antiraid/fakepermissions",
    "sudo": "sudo add/remove/ban/bot/cog/customize/guilds",
    "voice": "voicecentre setup/lock/unlock/limit/name/drag/permit/claim",
}


class Core(commands.Cog, name="Core"):
    """Core bot commands: prefix, AFK, help, and ping."""

    def __init__(self, bot: "Pushie") -> None:
        self.bot = bot

    # ======================== PING ========================
    @commands.command(name="ping")
    async def ping(self, ctx: "PushieContext") -> None:
        """Check the bot's response time."""
        await ctx.send(
            embed=UI.info(f"`{Emoji.PING}` *Pong! `{round(self.bot.latency * 1000)}ms`*")
        )

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
        """Activate AFK status."""
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
    async def help(self, ctx: "PushieContext", *, query: str | None = None) -> None:
        """Show help overview or help for a specific command/module."""
        if query is None:
            prefix = ctx.prefix or "!"
            lines = "\n".join(
                f"> `{mod}` — {cmds}" for mod, cmds in _MODULE_HELP.items()
            )
            embed = discord.Embed(
                description=(
                    f"`{Emoji.INFO}` **Pushie Help**\n\n"
                    f"{lines}\n\n"
                    f"> Use `{prefix}help <module>` for module detail\n"
                    f"> Use `{prefix}help <command>` for command detail\n"
                    f"> Use `{prefix}help variables` for embed vars"
                ),
                color=0xFAB9EC,
            )
            await ctx.send(embed=embed)
            return

        q = query.lower()
        if q == "variables":
            await ctx.send(
                embed=UI.info(
                    f"`{Emoji.INFO}` **Embed Substitution Variables**\n\n"
                    f"> **User Variables:**\n"
                    f"```\n$user.name — Display name\n"
                    f"$user.id — User ID\n"
                    f"$user.mention — @mention\n"
                    f"$user.discriminator — #tag\n```\n"
                    f"> **Server Variables:**\n"
                    f"```\n$guild.name — Server name\n"
                    f"$guild.id — Server ID\n"
                    f"$guild.members — Member count\n```"
                )
            )
            return

        # Check if it matches a cog name
        for cog_name, cog in self.bot.cogs.items():
            if cog_name.lower() == q:
                cmds = [c for c in cog.get_commands() if not c.hidden]
                prefix = ctx.prefix or "!"
                cmd_lines = "\n".join(
                    f"> `{prefix}{c.qualified_name}` — {c.short_doc or 'No description'}"
                    for c in cmds[:20]
                )
                embed = discord.Embed(
                    description=f"`{Emoji.INFO}` **{cog_name} Commands**\n\n{cmd_lines or '*No commands*'}",
                    color=0xFAB9EC,
                )
                await ctx.send(embed=embed)
                return

        # Check if it matches a command
        cmd = self.bot.get_command(q)
        if cmd:
            prefix = ctx.prefix or "!"
            aliases = ", ".join(f"`{a}`" for a in cmd.aliases) if cmd.aliases else "*none*"
            embed = discord.Embed(
                description=(
                    f"`{Emoji.INFO}` **`{prefix}{cmd.qualified_name}`**\n\n"
                    f"> {cmd.help or cmd.short_doc or 'No description'}\n\n"
                    f"> **Aliases:** {aliases}"
                ),
                color=0xFAB9EC,
            )
            if hasattr(cmd, 'commands'):
                subs = "\n".join(
                    f"> `{prefix}{s.qualified_name}` — {s.short_doc or ''}"
                    for s in cmd.commands  # type: ignore
                )
                embed.add_field(name="Subcommands", value=subs or "*none*", inline=False)
            await ctx.send(embed=embed)
            return

        await ctx.err(f"*No command or module found for `{query}`.*")

    @help.command(name="list")
    async def help_list(self, ctx: "PushieContext") -> None:
        """List all command modules."""
        cogs = sorted(self.bot.cogs.keys())
        lines = "\n".join(f"> `{c}`" for c in cogs)
        await ctx.send(
            embed=discord.Embed(
                description=f"`{Emoji.INFO}` **Available Modules**\n\n{lines}",
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
                f"```\n$user.name — Display name\n"
                f"$user.id — User ID\n"
                f"$user.mention — @mention\n```\n"
                f"> **Server Variables:**\n"
                f"```\n$guild.name — Server name\n"
                f"$guild.id — Server ID\n"
                f"$guild.members — Member count\n```"
            )
        )


async def setup(bot: "Pushie") -> None:
    await bot.add_cog(Core(bot))
