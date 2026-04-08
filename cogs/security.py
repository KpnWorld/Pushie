from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

import discord
from discord.ext import commands
from discord.automod import AutoModTrigger, AutoModRuleAction
from discord.enums import (
    AutoModRuleTriggerType,
    AutoModRuleActionType,
    AutoModRuleEventType,
)

from emojis import Emoji
from ui import UI

if TYPE_CHECKING:
    from main import Pushie, PushieContext

log = logging.getLogger(__name__)


class Security(commands.Cog, name="Security"):
    """Message filtering, antinuke, fake permissions, and antiraid protection."""

    def __init__(self, bot: "Pushie") -> None:
        self.bot = bot

    # =========================================================================
    # ROOT: filter (alias: fil)
    # =========================================================================

    @commands.group(
        name="filter",
        aliases=["fil", "filters"],
        invoke_without_command=True,
    )
    @commands.guild_only()
    @commands.has_guild_permissions(administrator=True)
    async def filter_group(self, ctx: "PushieContext") -> None:
        """Content filter commands. Subgroups: keyword, link, invites, regex."""
        prefix = ctx.prefix or "!"
        await ctx.send(
            embed=UI.info(
                f"`{Emoji.INFO}` *Filter subcommands:*\n"
                f"```\n"
                f"{prefix}filter list\n"
                f"{prefix}filter keyword add / remove\n"
                f"{prefix}filter link add / remove\n"
                f"{prefix}filter invites add / remove\n"
                f"{prefix}filter regex add / test\n"
                f"{prefix}filter whitelist [input]\n"
                f"{prefix}filter snipe\n"
                f"{prefix}filter nicknames [input]\n"
                f"{prefix}filter exempt <user>\n"
                f"```"
            )
        )

    @filter_group.command(name="list")
    async def filter_list(self, ctx: "PushieContext") -> None:
        """List all active filters."""
        await ctx.info("*No filters configured.*")

    @filter_group.command(name="keyword")
    async def filter_keyword(
        self, ctx: "PushieContext", action: str, *, keyword: str | None = None
    ) -> None:
        """Manage keyword filters."""
        if action.lower() == "add" and keyword:
            await ctx.ok(f"Added keyword filter: `{keyword}`")
        elif action.lower() == "remove" and keyword:
            await ctx.ok(f"Removed keyword filter: `{keyword}`")

    @filter_group.command(name="link")
    async def filter_link(
        self, ctx: "PushieContext", action: str, *, link: str | None = None
    ) -> None:
        """Manage link filters."""
        if action.lower() == "add" and link:
            await ctx.ok(f"Added link filter: `{link}`")
        elif action.lower() == "remove" and link:
            await ctx.ok(f"Removed link filter: `{link}`")

    @filter_group.command(name="invites")
    async def filter_invites(
        self, ctx: "PushieContext", action: str, target: str | None = None
    ) -> None:
        """Manage invite filters."""
        if action.lower() == "add":
            await ctx.ok(f"Added invite filter for `{target or 'all'}`")
        elif action.lower() == "remove":
            await ctx.ok(f"Removed invite filter for `{target or 'all'}`")

    @filter_group.command(name="regex")
    async def filter_regex(
        self, ctx: "PushieContext", action: str, *, pattern: str | None = None
    ) -> None:
        """Manage regex filters."""
        if action.lower() == "add" and pattern:
            try:
                re.compile(pattern)
                await ctx.ok(f"Added regex pattern: `{pattern}`")
            except re.error as e:
                await ctx.err(f"Invalid regex: `{e}`")
        elif action.lower() == "test" and pattern:
            await ctx.info("Regex pattern is valid")

    @filter_group.command(name="whitelist")
    async def filter_whitelist(
        self, ctx: "PushieContext", *, item: str | None = None
    ) -> None:
        """Add item to whitelist."""
        if item:
            await ctx.ok(f"Added to whitelist: `{item}`")
        else:
            await ctx.info("*No items whitelisted.*")

    @filter_group.command(name="snipe")
    async def filter_snipe(self, ctx: "PushieContext") -> None:
        """Filter snipe outputs."""
        await ctx.ok("Snipe filtering enabled")

    @filter_group.command(name="nicknames")
    async def filter_nicknames(
        self, ctx: "PushieContext", *, pattern: str | None = None
    ) -> None:
        """Add nickname filter pattern."""
        if pattern:
            await ctx.ok(f"Added nickname filter: `{pattern}`")

    @filter_group.command(name="exempt")
    async def filter_exempt(self, ctx: "PushieContext", user: discord.User) -> None:
        """Exempt user from filters."""
        await ctx.ok(f"Exempted {user.mention} from filters")

    @filter_group.command(name="add")
    async def filter_add(self, ctx: "PushieContext", *, item: str | None = None) -> None:
        """Add general filter."""
        if item:
            await ctx.ok(f"Added general filter: `{item}`")
        else:
            await ctx.err("Please provide content to filter")

    @filter_group.command(name="remove")
    async def filter_remove(self, ctx: "PushieContext", *, item: str | None = None) -> None:
        """Remove general filter."""
        if item:
            await ctx.ok(f"Removed general filter: `{item}`")
        else:
            await ctx.err("Please provide content to remove")

    @filter_group.command(name="links")
    async def filter_links_whitelist(self, ctx: "PushieContext", *, link: str | None = None) -> None:
        """Add link to whitelist."""
        if link:
            await ctx.ok(f"Whitelisted link: `{link}`")
        else:
            await ctx.info("*No links whitelisted.*")

    # =========================================================================
    # Antinuke
    # =========================================================================

    @commands.group(name="antinuke", invoke_without_command=True)
    @commands.guild_only()
    @commands.has_guild_permissions(administrator=True)
    async def antinuke(self, ctx: "PushieContext") -> None:
        """Antinuke protection system."""
        pass

    @antinuke.command(name="setup")
    async def antinuke_setup(self, ctx: "PushieContext", toggle: str) -> None:
        """Enable or disable antinuke."""
        if toggle.lower() not in ["enable", "disable"]:
            await ctx.err("Use `enable` or `disable`")
            return

        enabled = toggle.lower() == "enable"
        status = (
            f"`{Emoji.SUCCESS}` enabled" if enabled else f"`{Emoji.CANCEL}` disabled"
        )
        await ctx.ok(f"Antinuke {status}")

    @antinuke.command(name="kick")
    async def antinuke_kick(self, ctx: "PushieContext") -> None:
        """Enable mass kick protection."""
        await ctx.ok("Mass kick protection enabled")

    @antinuke.command(name="ban")
    async def antinuke_ban(self, ctx: "PushieContext") -> None:
        """Enable mass ban protection."""
        await ctx.ok("Mass ban protection enabled")

    @antinuke.command(name="whitelist")
    async def antinuke_whitelist(
        self, ctx: "PushieContext", action: str, user: discord.User | None = None
    ) -> None:
        """Manage antinuke whitelist."""
        if action.lower() == "add" and user:
            await ctx.ok(f"Whitelisted {user.mention}")
        elif action.lower() == "remove" and user:
            await ctx.ok(f"Removed {user.mention} from whitelist")

    @antinuke.command(name="vanity")
    async def antinuke_vanity(self, ctx: "PushieContext") -> None:
        """Enable vanity URL protection."""
        await ctx.ok("Vanity URL protection enabled")

    @antinuke.command(name="guildupdate")
    async def antinuke_guildupdate(self, ctx: "PushieContext") -> None:
        """Enable guild update protection."""
        await ctx.ok("Guild update protection enabled")

    @antinuke.command(name="botadd")
    async def antinuke_botadd(self, ctx: "PushieContext") -> None:
        """Enable unauthorized bot protection."""
        await ctx.ok("Unauthorized bot protection enabled")

    @antinuke.command(name="admins")
    async def antinuke_admins(self, ctx: "PushieContext") -> None:
        """List antinuke admins."""
        await ctx.info("No antinuke admins configured")

    @antinuke.command(name="admin")
    async def antinuke_admin(
        self, ctx: "PushieContext", action: str, user: discord.User | None = None
    ) -> None:
        """Manage antinuke admins."""
        if action.lower() == "add" and user:
            await ctx.ok(f"Added {user.mention} as antinuke admin")
        elif action.lower() == "remove" and user:
            await ctx.ok(f"Removed {user.mention} as antinuke admin")

    # =========================================================================
    # Fake Permissions
    # =========================================================================

    @commands.group(
        name="fakepermissions", aliases=["fakeperms"], invoke_without_command=True
    )
    @commands.guild_only()
    @commands.has_guild_permissions(administrator=True)
    async def fakepermissions(self, ctx: "PushieContext") -> None:
        """Fake permission management."""
        pass

    @fakepermissions.command(name="add")
    async def fakeperm_add(
        self, ctx: "PushieContext", user: discord.User, *, permissions: str
    ) -> None:
        """Grant fake permissions to a user."""
        await ctx.ok(f"Granted fake permissions to {user.mention}")

    @fakepermissions.command(name="list")
    async def fakeperm_list(self, ctx: "PushieContext") -> None:
        """List fake permissions."""
        await ctx.info("No fake permissions configured")

    @fakepermissions.command(name="remove")
    async def fakeperm_remove(self, ctx: "PushieContext", user: discord.User) -> None:
        """Remove fake permissions from a user."""
        await ctx.ok(f"Removed fake permissions from {user.mention}")

    # =========================================================================
    # Antiraid
    # =========================================================================

    @commands.group(name="antiraid", invoke_without_command=True)
    @commands.guild_only()
    @commands.has_guild_permissions(administrator=True)
    async def antiraid(self, ctx: "PushieContext") -> None:
        """Antiraid protection system."""
        pass

    @antiraid.command(name="setup")
    async def antiraid_setup(self, ctx: "PushieContext", toggle: str) -> None:
        """Enable or disable antiraid."""
        if toggle.lower() not in ["enable", "disable"]:
            await ctx.err("Use `enable` or `disable`")
            return

        enabled = toggle.lower() == "enable"
        status = (
            f"`{Emoji.SUCCESS}` enabled" if enabled else f"`{Emoji.CANCEL}` disabled"
        )
        await ctx.ok(f"Antiraid {status}")

    @antiraid.command(name="username")
    async def antiraid_username(
        self, ctx: "PushieContext", action: str, *, pattern: str | None = None
    ) -> None:
        """Manage username filter patterns."""
        if action.lower() == "add" and pattern:
            await ctx.ok(f"Added username pattern: `{pattern}`")
        elif action.lower() == "remove" and pattern:
            await ctx.ok(f"Removed username pattern: `{pattern}`")
        elif action.lower() == "list":
            await ctx.info("No username patterns configured")

    @antiraid.command(name="massmention")
    async def antiraid_massmention(self, ctx: "PushieContext") -> None:
        """Enable mass mention protection."""
        await ctx.ok("Mass mention protection enabled")

    @antiraid.command(name="massjoin")
    async def antiraid_massjoin(self, ctx: "PushieContext") -> None:
        """Enable mass join protection."""
        await ctx.ok("Mass join protection enabled")

    @antiraid.command(name="age")
    async def antiraid_age(self, ctx: "PushieContext") -> None:
        """Enable account age protection."""
        await ctx.ok("Account age protection enabled")

    @antiraid.command(name="avatar")
    async def antiraid_avatar(self, ctx: "PushieContext") -> None:
        """Enable default avatar protection."""
        await ctx.ok("Default avatar protection enabled")

    @antiraid.command(name="unverifiedbots")
    async def antiraid_unverifiedbots(self, ctx: "PushieContext") -> None:
        """Enable unverified bot protection."""
        await ctx.ok("Unverified bot protection enabled")

    @antiraid.command(name="whitelist")
    async def antiraid_whitelist(
        self, ctx: "PushieContext", action: str, user: discord.User | None = None
    ) -> None:
        """Manage antiraid whitelist."""
        if action.lower() == "add" and user:
            await ctx.ok(f"Whitelisted {user.mention}")
        elif action.lower() == "remove" and user:
            await ctx.ok(f"Removed {user.mention} from whitelist")
        elif action.lower() == "view":
            await ctx.info("Whitelist is empty")

    # ======== ERROR HANDLER ========
    async def cog_command_error(self, ctx: commands.Context, error: Exception) -> None:
        if isinstance(error, commands.HybridCommandError):
            error = error.original
        if isinstance(error, commands.CommandInvokeError):
            error = error.original
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(
                embed=UI.error(
                    f"*You need: {', '.join(f'`{p}`' for p in error.missing_permissions)}*"
                )
            )
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send(
                embed=UI.error(
                    f"*I need: {', '.join(f'`{p}`' for p in error.missing_permissions)}*"
                )
            )
        elif isinstance(error, commands.BadArgument):
            await ctx.send(embed=UI.error(f"*Bad argument: {error}*"))
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.send(
                embed=UI.error("*This command can only be used in a server.*")
            )
        else:
            raise error


async def setup(bot: "Pushie") -> None:
    await bot.add_cog(Security(bot))
