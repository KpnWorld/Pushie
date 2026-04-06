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


class Filters(commands.Cog, name="Filters"):
    """Message filtering and content moderation via Discord AutoMod."""

    def __init__(self, bot: "Pushie") -> None:
        self.bot = bot

    # =========================================================================
    # ROOT: filter (alias: f)
    # =========================================================================

    @commands.hybrid_group(
        name="filter",
        aliases=["f", "filters"],
        description="Manage content filters",
        invoke_without_command=True,
    )
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def filter_group(self, ctx: "PushieContext") -> None:
        """Content filter commands. Subgroups: link, word, mention, caps."""
        prefix = ctx.prefix or "!"
        await ctx.send(
            embed=UI.info(
                f"`{Emoji.INFO}` *Filter subcommands:*\n"
                f"```\n"
                f"{prefix}filter link   add / remove / list\n"
                f"{prefix}filter word   add / remove / list\n"
                f"{prefix}filter mention set / remove / list\n"
                f"{prefix}filter caps   set / remove\n"
                f"{prefix}filter reset\n"
                f"```"
            )
        )

    # =========================================================================
    # filter link  (alias: lk)
    # =========================================================================

    @filter_group.group(
        name="link",
        aliases=["lk", "links"],
        description="Manage link filters",
        invoke_without_command=True,
    )
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def filter_link(self, ctx: "PushieContext") -> None:
        """Link filter — subcommands: add, remove, list."""
        prefix = ctx.prefix or "!"
        await ctx.send(
            embed=UI.info(f"*Use `{prefix}filter link add/remove/list`*")
        )

    @filter_link.command(name="add", aliases=["a", "+"])
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def filter_link_add(self, ctx: "PushieContext", *, pattern: str) -> None:
        """Add a regex pattern to the link filter."""
        assert ctx.guild is not None
        try:
            re.compile(pattern)
        except re.error as e:
            await ctx.err(f"*Invalid regex: `{e}`*")
            return
        try:
            rules = await ctx.guild.fetch_automod_rules()
            rule = next((r for r in rules if r.name == "pushie_link_filter"), None)
            if rule:
                patterns = list(rule.trigger.regex_patterns or [])
                if pattern in patterns:
                    await ctx.err("*This pattern is already in the filter.*")
                    return
                patterns.append(pattern)
                await rule.edit(
                    trigger=AutoModTrigger(
                        type=AutoModRuleTriggerType.keyword,
                        regex_patterns=patterns,
                    )
                )
            else:
                await ctx.guild.create_automod_rule(
                    name="pushie_link_filter",
                    event_type=AutoModRuleEventType.message_send,
                    trigger=AutoModTrigger(
                        type=AutoModRuleTriggerType.keyword,
                        regex_patterns=[pattern],
                    ),
                    actions=[AutoModRuleAction(type=AutoModRuleActionType.block_message)],
                    enabled=True,
                    reason="Link filter created via Pushie",
                )
            await ctx.ok(f"`{Emoji.INFO}` *Link filter added: `{pattern}`*")
        except discord.Forbidden:
            await ctx.err("*I need Manage Guild to edit AutoMod rules.*")
        except discord.HTTPException as e:
            await ctx.err(f"*Failed: `{e}`*")

    @filter_link.command(name="remove", aliases=["rm", "del", "-"])
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def filter_link_remove(self, ctx: "PushieContext", *, pattern: str) -> None:
        """Remove a regex pattern from the link filter."""
        assert ctx.guild is not None
        try:
            rules = await ctx.guild.fetch_automod_rules()
            rule = next((r for r in rules if r.name == "pushie_link_filter"), None)
            if not rule:
                await ctx.err("*No link filters configured.*")
                return
            patterns = list(rule.trigger.regex_patterns or [])
            if pattern not in patterns:
                await ctx.err("*Pattern not found in filter.*")
                return
            patterns.remove(pattern)
            if patterns:
                await rule.edit(
                    trigger=AutoModTrigger(
                        type=AutoModRuleTriggerType.keyword,
                        regex_patterns=patterns,
                    )
                )
            else:
                await rule.delete()
            await ctx.ok(f"`{Emoji.INFO}` *Link filter removed: `{pattern}`*")
        except discord.Forbidden:
            await ctx.err("*Missing permissions to manage AutoMod rules.*")
        except discord.HTTPException as e:
            await ctx.err(f"*Failed: `{e}`*")

    @filter_link.command(name="list", aliases=["ls", "show", "all"])
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def filter_link_list(self, ctx: "PushieContext") -> None:
        """List all link filter patterns."""
        assert ctx.guild is not None
        try:
            rules = await ctx.guild.fetch_automod_rules()
            rule = next((r for r in rules if r.name == "pushie_link_filter"), None)
            if not rule or not rule.trigger.regex_patterns:
                await ctx.info("*No link filters configured.*")
                return
            patterns = rule.trigger.regex_patterns
            text = "\n".join(f"> `{i+1}.` `{p}`" for i, p in enumerate(patterns[:10]))
            extra = f"\n> *+{len(patterns) - 10} more...*" if len(patterns) > 10 else ""
            await ctx.send(
                embed=discord.Embed(
                    description=f"`{Emoji.INFO}` *Link Filters ({len(patterns)})*\n\n{text}{extra}",
                    color=0xFAB9EC,
                )
            )
        except discord.Forbidden:
            await ctx.err("*Missing permissions.*")
        except discord.HTTPException as e:
            await ctx.err(f"*Failed: `{e}`*")

    # =========================================================================
    # filter word  (alias: w)
    # =========================================================================

    @filter_group.group(
        name="word",
        aliases=["w", "words"],
        description="Manage word filters",
        invoke_without_command=True,
    )
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def filter_word(self, ctx: "PushieContext") -> None:
        """Word filter — subcommands: add, remove, list."""
        prefix = ctx.prefix or "!"
        await ctx.send(
            embed=UI.info(f"*Use `{prefix}filter word add/remove/list`*")
        )

    @filter_word.command(name="add", aliases=["a", "+"])
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def filter_word_add(self, ctx: "PushieContext", *, word: str) -> None:
        """Add a word to the word filter."""
        assert ctx.guild is not None
        try:
            rules = await ctx.guild.fetch_automod_rules()
            rule = next((r for r in rules if r.name == "pushie_word_filter"), None)
            if rule:
                words = list(rule.trigger.keyword_filter or [])
                if word in words:
                    await ctx.err("*This word is already filtered.*")
                    return
                words.append(word)
                await rule.edit(
                    trigger=AutoModTrigger(
                        type=AutoModRuleTriggerType.keyword,
                        keyword_filter=words,
                    )
                )
            else:
                await ctx.guild.create_automod_rule(
                    name="pushie_word_filter",
                    event_type=AutoModRuleEventType.message_send,
                    trigger=AutoModTrigger(
                        type=AutoModRuleTriggerType.keyword,
                        keyword_filter=[word],
                    ),
                    actions=[AutoModRuleAction(type=AutoModRuleActionType.block_message)],
                    enabled=True,
                    reason="Word filter created via Pushie",
                )
            await ctx.ok(f"`{Emoji.INFO}` *Word added to filter: `{word}`*")
        except discord.Forbidden:
            await ctx.err("*Missing permissions to manage AutoMod rules.*")
        except discord.HTTPException as e:
            await ctx.err(f"*Failed: `{e}`*")

    @filter_word.command(name="remove", aliases=["rm", "del", "-"])
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def filter_word_remove(self, ctx: "PushieContext", *, word: str) -> None:
        """Remove a word from the word filter."""
        assert ctx.guild is not None
        try:
            rules = await ctx.guild.fetch_automod_rules()
            rule = next((r for r in rules if r.name == "pushie_word_filter"), None)
            if not rule:
                await ctx.err("*No word filters configured.*")
                return
            words = list(rule.trigger.keyword_filter or [])
            if word not in words:
                await ctx.err("*Word not found in filter.*")
                return
            words.remove(word)
            if words:
                await rule.edit(
                    trigger=AutoModTrigger(
                        type=AutoModRuleTriggerType.keyword,
                        keyword_filter=words,
                    )
                )
            else:
                await rule.delete()
            await ctx.ok(f"`{Emoji.INFO}` *Word removed from filter: `{word}`*")
        except discord.Forbidden:
            await ctx.err("*Missing permissions.*")
        except discord.HTTPException as e:
            await ctx.err(f"*Failed: `{e}`*")

    @filter_word.command(name="list", aliases=["ls", "show", "all"])
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def filter_word_list(self, ctx: "PushieContext") -> None:
        """List all filtered words."""
        assert ctx.guild is not None
        try:
            rules = await ctx.guild.fetch_automod_rules()
            rule = next((r for r in rules if r.name == "pushie_word_filter"), None)
            if not rule or not rule.trigger.keyword_filter:
                await ctx.info("*No word filters configured.*")
                return
            words = rule.trigger.keyword_filter
            text = "\n".join(f"> `{i+1}.` `{w}`" for i, w in enumerate(words[:10]))
            extra = f"\n> *+{len(words) - 10} more...*" if len(words) > 10 else ""
            await ctx.send(
                embed=discord.Embed(
                    description=f"`{Emoji.INFO}` *Filtered Words ({len(words)})*\n\n{text}{extra}",
                    color=0xFAB9EC,
                )
            )
        except discord.Forbidden:
            await ctx.err("*Missing permissions.*")
        except discord.HTTPException as e:
            await ctx.err(f"*Failed: `{e}`*")

    # =========================================================================
    # filter mention  (alias: m)
    # =========================================================================

    @filter_group.group(
        name="mention",
        aliases=["m", "mentions"],
        description="Manage mention spam filters",
        invoke_without_command=True,
    )
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def filter_mention(self, ctx: "PushieContext") -> None:
        """Mention filter — subcommands: set, remove, list."""
        prefix = ctx.prefix or "!"
        await ctx.send(
            embed=UI.info(f"*Use `{prefix}filter mention set/remove/list`*")
        )

    @filter_mention.command(name="set", aliases=["add", "s", "a"])
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def filter_mention_set(
        self, ctx: "PushieContext", limit: int = 5
    ) -> None:
        """Set the max allowed mentions per message (1–50)."""
        assert ctx.guild is not None
        if not (1 <= limit <= 50):
            await ctx.err("*Limit must be between `1` and `50`.*")
            return
        try:
            rules = await ctx.guild.fetch_automod_rules()
            rule = next((r for r in rules if r.name == "pushie_mention_filter"), None)
            trigger = AutoModTrigger(
                type=AutoModRuleTriggerType.mention_spam, mention_limit=limit
            )
            if rule:
                await rule.edit(trigger=trigger)
            else:
                await ctx.guild.create_automod_rule(
                    name="pushie_mention_filter",
                    event_type=AutoModRuleEventType.message_send,
                    trigger=trigger,
                    actions=[AutoModRuleAction(type=AutoModRuleActionType.block_message)],
                    enabled=True,
                    reason="Mention filter created via Pushie",
                )
            await ctx.ok(f"`{Emoji.INFO}` *Mention limit set to `{limit}`.*")
        except discord.Forbidden:
            await ctx.err("*Missing permissions.*")
        except discord.HTTPException as e:
            await ctx.err(f"*Failed: `{e}`*")

    @filter_mention.command(name="remove", aliases=["rm", "disable", "off"])
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def filter_mention_remove(self, ctx: "PushieContext") -> None:
        """Disable mention spam filtering."""
        assert ctx.guild is not None
        try:
            rules = await ctx.guild.fetch_automod_rules()
            rule = next((r for r in rules if r.name == "pushie_mention_filter"), None)
            if not rule:
                await ctx.err("*Mention filtering is not configured.*")
                return
            await rule.delete()
            await ctx.ok(f"`{Emoji.INFO}` *Mention filtering disabled.*")
        except discord.Forbidden:
            await ctx.err("*Missing permissions.*")
        except discord.HTTPException as e:
            await ctx.err(f"*Failed: `{e}`*")

    @filter_mention.command(name="list", aliases=["ls", "show", "status"])
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def filter_mention_list(self, ctx: "PushieContext") -> None:
        """Show current mention filter settings."""
        assert ctx.guild is not None
        try:
            rules = await ctx.guild.fetch_automod_rules()
            rule = next((r for r in rules if r.name == "pushie_mention_filter"), None)
            if not rule:
                await ctx.info("*No mention filter configured.*")
                return
            await ctx.send(
                embed=discord.Embed(
                    description=(
                        f"`{Emoji.INFO}` *Mention Filter*\n\n"
                        f"> **Limit:** `{rule.trigger.mention_limit}` per message\n"
                        f"> **Raid Protection:** `{rule.trigger.mention_raid_protection}`"
                    ),
                    color=0xFAB9EC,
                )
            )
        except discord.Forbidden:
            await ctx.err("*Missing permissions.*")
        except discord.HTTPException as e:
            await ctx.err(f"*Failed: `{e}`*")

    # =========================================================================
    # filter caps  (alias: c)
    # =========================================================================

    @filter_group.group(
        name="caps",
        aliases=["c", "capslock"],
        description="Caps filter (Discord AutoMod does not natively support caps %)",
        invoke_without_command=True,
    )
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def filter_caps(self, ctx: "PushieContext") -> None:
        """Caps filter — subcommands: set, remove."""
        prefix = ctx.prefix or "!"
        await ctx.send(
            embed=UI.info(f"*Use `{prefix}filter caps set/remove`*")
        )

    @filter_caps.command(name="set", aliases=["add", "s", "a"])
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def filter_caps_set(
        self, ctx: "PushieContext", threshold: int = 70
    ) -> None:
        """Note: Discord AutoMod does not support caps-% filtering natively."""
        await ctx.warn(
            "*Discord AutoMod does not natively support caps-percentage filtering.*\n"
            f"*Use `{ctx.prefix}filter word add WORD` to block specific all-caps words.*"
        )

    @filter_caps.command(name="remove", aliases=["rm", "disable", "off"])
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def filter_caps_remove(self, ctx: "PushieContext") -> None:
        """Disable caps filtering (no-op — see note on `filter caps set`)."""
        await ctx.info("*Caps percentage filtering is not available via Discord AutoMod.*")

    # =========================================================================
    # filter reset  (alias: r)
    # =========================================================================

    @filter_group.command(name="reset", aliases=["r", "clear", "wipe"])
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def filter_reset(self, ctx: "PushieContext") -> None:
        """Delete all Pushie-managed AutoMod filter rules for this server."""
        assert ctx.guild is not None
        try:
            rules = await ctx.guild.fetch_automod_rules()
            managed = [
                r
                for r in rules
                if r.name in (
                    "pushie_link_filter",
                    "pushie_word_filter",
                    "pushie_mention_filter",
                    "pushie_caps_filter",
                    # legacy names
                    "link_filter",
                    "word_filter",
                    "mention_filter",
                    "caps_filter",
                )
            ]
            if not managed:
                await ctx.info("*No Pushie filter rules to reset.*")
                return
            for rule in managed:
                await rule.delete()
            await ctx.ok(
                f"`{Emoji.RESET}` *Reset `{len(managed)}` filter rule(s).*"
            )
        except discord.Forbidden:
            await ctx.err("*Missing permissions to manage AutoMod rules.*")
        except discord.HTTPException as e:
            await ctx.err(f"*Failed: `{e}`*")

    # =========================================================================
    # ERROR HANDLER
    # =========================================================================

    async def cog_command_error(
        self, ctx: commands.Context, error: Exception
    ) -> None:
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
    await bot.add_cog(Filters(bot))
