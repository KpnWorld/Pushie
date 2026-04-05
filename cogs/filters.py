from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING, cast
from datetime import timedelta

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
    """Message filtering and content moderation."""

    def __init__(self, bot: "Pushie") -> None:
        self.bot = bot

    # =========================================================================
    # LINK FILTERS
    # =========================================================================

    @commands.hybrid_group(name="link", description="Manage link filtering")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def link(self, ctx: "PushieContext") -> None:
        """Link filter management."""
        pass

    @link.command(name="add", description="Add a link filter pattern (regex)")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def link_add(self, ctx: "PushieContext", *, pattern: str) -> None:
        """Add a link filter pattern as a regex."""
        assert ctx.guild is not None
        try:
            re.compile(pattern)
        except re.error as e:
            await ctx.err(f"*Invalid regex pattern: `{e}`*")
            return

        try:
            # Fetch existing rules to get current patterns
            rules = await ctx.guild.fetch_automod_rules()
            link_rule = next((r for r in rules if r.name == "link_filter"), None)

            if link_rule:
                # Update existing rule with new pattern
                current_patterns = link_rule.trigger.regex_patterns or []
                if pattern not in current_patterns:
                    current_patterns.append(pattern)
                    new_trigger = AutoModTrigger(
                        type=AutoModRuleTriggerType.keyword,
                        regex_patterns=current_patterns,
                    )
                    await link_rule.edit(trigger=new_trigger)
                    await ctx.ok(f"`{Emoji.INFO}` *Link filter updated: `{pattern}`*")
                else:
                    await ctx.err("*This pattern is already in the filter.*")
            else:
                # Create new rule
                trigger = AutoModTrigger(
                    type=AutoModRuleTriggerType.keyword, regex_patterns=[pattern]
                )
                action = AutoModRuleAction(type=AutoModRuleActionType.block_message)
                await ctx.guild.create_automod_rule(
                    name="link_filter",
                    event_type=AutoModRuleEventType.message_send,
                    trigger=trigger,
                    actions=[action],
                    enabled=True,
                    reason="Created via link filter command",
                )
                await ctx.ok(f"`{Emoji.INFO}` *Link filter added: `{pattern}`*")
        except discord.Forbidden:
            await ctx.err("*I don't have permission to manage automod rules.*")
        except discord.HTTPException as e:
            await ctx.err(f"*Failed to add link filter: `{e}`*")

    @link.command(name="remove", description="Remove a link filter")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def link_remove(self, ctx: "PushieContext", *, pattern: str) -> None:
        """Remove a link filter pattern."""
        assert ctx.guild is not None
        try:
            rules = await ctx.guild.fetch_automod_rules()
            link_rule = next((r for r in rules if r.name == "link_filter"), None)

            if not link_rule:
                await ctx.err("*No link filters are configured.*")
                return

            current_patterns = link_rule.trigger.regex_patterns or []
            if pattern in current_patterns:
                current_patterns.remove(pattern)

                if current_patterns:
                    # Update rule with remaining patterns
                    new_trigger = AutoModTrigger(
                        type=AutoModRuleTriggerType.keyword,
                        regex_patterns=current_patterns,
                    )
                    await link_rule.edit(trigger=new_trigger)
                    await ctx.ok(f"`{Emoji.INFO}` *Link filter removed: `{pattern}`*")
                else:
                    # Delete the rule if no patterns left
                    await link_rule.delete()
                    await ctx.ok(
                        f"`{Emoji.INFO}` *Link filter `{pattern}` removed. Rule deleted.*"
                    )
            else:
                await ctx.err("*This pattern is not in the filter.*")
        except discord.Forbidden:
            await ctx.err("*I don't have permission to manage automod rules.*")
        except discord.HTTPException as e:
            await ctx.err(f"*Failed to remove link filter: `{e}`*")

    @link.command(name="list", description="List all link filters")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def link_list(self, ctx: "PushieContext") -> None:
        """View all link filter patterns."""
        assert ctx.guild is not None
        try:
            rules = await ctx.guild.fetch_automod_rules()
            link_rule = next((r for r in rules if r.name == "link_filter"), None)

            if not link_rule or not link_rule.trigger.regex_patterns:
                await ctx.info("*No link filters configured.*")
                return

            patterns = link_rule.trigger.regex_patterns
            filter_text = "\n".join(
                f"> `{i+1}.` `{p}`" for i, p in enumerate(patterns[:10])
            )
            extra = f"\n> *+{len(patterns) - 10} more...*" if len(patterns) > 10 else ""

            embed = discord.Embed(
                description=f"`{Emoji.INFO}` *Link Filters ({len(patterns)} total)*\n\n{filter_text}{extra}",
                color=0xFAB9EC,
            )
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.err("*I don't have permission to view automod rules.*")
        except discord.HTTPException as e:
            await ctx.err(f"*Failed to fetch link filters: `{e}`*")

    # =========================================================================
    # WORD FILTERS
    # =========================================================================

    @commands.hybrid_group(name="word", description="Manage word filtering")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def word(self, ctx: "PushieContext") -> None:
        """Word filter management."""
        pass

    @word.command(name="add", description="Add a word to filter")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def word_add(self, ctx: "PushieContext", *, word: str) -> None:
        """Add a word to the word filter."""
        assert ctx.guild is not None
        try:
            rules = await ctx.guild.fetch_automod_rules()
            word_rule = next((r for r in rules if r.name == "word_filter"), None)

            if word_rule:
                # Update existing rule
                current_words = word_rule.trigger.keyword_filter or []
                if word not in current_words:
                    current_words.append(word)
                    new_trigger = AutoModTrigger(
                        type=AutoModRuleTriggerType.keyword,
                        keyword_filter=current_words,
                    )
                    await word_rule.edit(trigger=new_trigger)
                    await ctx.ok(f"`{Emoji.INFO}` *Word filter updated: `{word}`*")
                else:
                    await ctx.err("*This word is already in the filter.*")
            else:
                # Create new rule
                trigger = AutoModTrigger(
                    type=AutoModRuleTriggerType.keyword, keyword_filter=[word]
                )
                action = AutoModRuleAction(type=AutoModRuleActionType.block_message)
                await ctx.guild.create_automod_rule(
                    name="word_filter",
                    event_type=AutoModRuleEventType.message_send,
                    trigger=trigger,
                    actions=[action],
                    enabled=True,
                    reason="Created via word filter command",
                )
                await ctx.ok(f"`{Emoji.INFO}` *Word filter added: `{word}`*")
        except discord.Forbidden:
            await ctx.err("*I don't have permission to manage automod rules.*")
        except discord.HTTPException as e:
            await ctx.err(f"*Failed to add word filter: `{e}`*")

    @word.command(name="remove", description="Remove a word from filter")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def word_remove(self, ctx: "PushieContext", *, word: str) -> None:
        """Remove a word from the word filter."""
        assert ctx.guild is not None
        try:
            rules = await ctx.guild.fetch_automod_rules()
            word_rule = next((r for r in rules if r.name == "word_filter"), None)

            if not word_rule:
                await ctx.err("*No word filters are configured.*")
                return

            current_words = word_rule.trigger.keyword_filter or []
            if word in current_words:
                current_words.remove(word)

                if current_words:
                    new_trigger = AutoModTrigger(
                        type=AutoModRuleTriggerType.keyword,
                        keyword_filter=current_words,
                    )
                    await word_rule.edit(trigger=new_trigger)
                    await ctx.ok(f"`{Emoji.INFO}` *Word filter removed: `{word}`*")
                else:
                    await word_rule.delete()
                    await ctx.ok(
                        f"`{Emoji.INFO}` *Word `{word}` removed. Rule deleted.*"
                    )
            else:
                await ctx.err("*This word is not in the filter.*")
        except discord.Forbidden:
            await ctx.err("*I don't have permission to manage automod rules.*")
        except discord.HTTPException as e:
            await ctx.err(f"*Failed to remove word filter: `{e}`*")

    @word.command(name="list", description="List all filtered words")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def word_list(self, ctx: "PushieContext") -> None:
        """View all filtered words."""
        assert ctx.guild is not None
        try:
            rules = await ctx.guild.fetch_automod_rules()
            word_rule = next((r for r in rules if r.name == "word_filter"), None)

            if not word_rule or not word_rule.trigger.keyword_filter:
                await ctx.info("*No word filters configured.*")
                return

            words = word_rule.trigger.keyword_filter
            filter_text = "\n".join(
                f"> `{i+1}.` `{w}`" for i, w in enumerate(words[:10])
            )
            extra = f"\n> *+{len(words) - 10} more...*" if len(words) > 10 else ""

            embed = discord.Embed(
                description=f"`{Emoji.INFO}` *Filtered Words ({len(words)} total)*\n\n{filter_text}{extra}",
                color=0xFAB9EC,
            )
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.err("*I don't have permission to view automod rules.*")
        except discord.HTTPException as e:
            await ctx.err(f"*Failed to fetch word filters: `{e}`*")

    # =========================================================================
    # MENTION FILTERS
    # =========================================================================

    @commands.hybrid_group(name="mention", description="Manage mention filtering")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def mention(self, ctx: "PushieContext") -> None:
        """Mention filter management."""
        pass

    @mention.command(name="add", description="Add mention spam filter")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def mention_add(self, ctx: "PushieContext", limit: int = 5) -> None:
        """Set maximum allowed mentions per message."""
        assert ctx.guild is not None
        if limit < 1 or limit > 50:
            await ctx.err("*Limit must be between `1` and `50`.*")
            return

        try:
            rules = await ctx.guild.fetch_automod_rules()
            mention_rule = next((r for r in rules if r.name == "mention_filter"), None)

            trigger = AutoModTrigger(
                type=AutoModRuleTriggerType.mention_spam, mention_limit=limit
            )
            action = AutoModRuleAction(type=AutoModRuleActionType.block_message)

            if mention_rule:
                await mention_rule.edit(trigger=trigger)
                await ctx.ok(f"`{Emoji.INFO}` *Mention limit updated to `{limit}`.*")
            else:
                await ctx.guild.create_automod_rule(
                    name="mention_filter",
                    event_type=AutoModRuleEventType.message_send,
                    trigger=trigger,
                    actions=[action],
                    enabled=True,
                    reason="Created via mention filter command",
                )
                await ctx.ok(f"`{Emoji.INFO}` *Mention limit set to `{limit}`.*")
        except discord.Forbidden:
            await ctx.err("*I don't have permission to manage automod rules.*")
        except discord.HTTPException as e:
            await ctx.err(f"*Failed to set mention filter: `{e}`*")

    @mention.command(name="remove", description="Disable mention filtering")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def mention_remove(self, ctx: "PushieContext") -> None:
        """Disable mention spam filtering."""
        assert ctx.guild is not None
        try:
            rules = await ctx.guild.fetch_automod_rules()
            mention_rule = next((r for r in rules if r.name == "mention_filter"), None)

            if mention_rule:
                await mention_rule.delete()
                await ctx.ok(f"`{Emoji.INFO}` *Mention filtering disabled.*")
            else:
                await ctx.err("*Mention filtering is not configured.*")
        except discord.Forbidden:
            await ctx.err("*I don't have permission to manage automod rules.*")
        except discord.HTTPException as e:
            await ctx.err(f"*Failed to disable mention filter: `{e}`*")

    @mention.command(name="list", description="View mention filter settings")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def mention_list(self, ctx: "PushieContext") -> None:
        """View mention filter configuration."""
        assert ctx.guild is not None
        try:
            rules = await ctx.guild.fetch_automod_rules()
            mention_rule = next((r for r in rules if r.name == "mention_filter"), None)

            if not mention_rule:
                await ctx.info("*No mention filters configured.*")
                return

            limit = mention_rule.trigger.mention_limit
            raid_protection = mention_rule.trigger.mention_raid_protection

            embed = discord.Embed(
                description=f"`{Emoji.INFO}` *Mention Filter Settings*\n\n> **Limit:** `{limit}` mentions\n> **Raid Protection:** `{raid_protection}`",
                color=0xFAB9EC,
            )
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.err("*I don't have permission to view automod rules.*")
        except discord.HTTPException as e:
            await ctx.err(f"*Failed to fetch mention filter: `{e}`*")

    # =========================================================================
    # CAPS FILTERS
    # =========================================================================

    @commands.hybrid_group(name="caps", description="Manage excessive caps filtering")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def caps(self, ctx: "PushieContext") -> None:
        """Excessive caps filter management."""
        pass

    @caps.command(name="add", description="Set caps spam threshold")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def caps_add(self, ctx: "PushieContext", threshold: int = 70) -> None:
        """Set caps percentage threshold (0-100)."""
        assert ctx.guild is not None
        if threshold < 0 or threshold > 100:
            await ctx.err("*Threshold must be between `0` and `100`.*")
            return

        try:
            # Note: Discord's AutoMod doesn't have a direct caps filter, so we'll use keyword_preset with CAPS_LOCK
            rules = await ctx.guild.fetch_automod_rules()
            caps_rule = next((r for r in rules if r.name == "caps_filter"), None)

            # Discord doesn't have native caps filter, so we'll create a placeholder
            # Store the threshold in the bot's storage instead
            g = self.bot.storage.get_guild_sync(ctx.guild.id)
            if not g:
                await ctx.err("*Guild data not initialized.*")
                return

            # This is a limitation - Discord AutoMod doesn't filter caps directly
            # But we can use the storage to enable caps filtering through bot logic
            await ctx.warn(
                "*Discord AutoMod doesn't support native caps filtering. Consider using word filters or mention filters instead.*"
            )
        except discord.Forbidden:
            await ctx.err("*I don't have permission to manage automod rules.*")
        except discord.HTTPException as e:
            await ctx.err(f"*Failed to set caps filter: `{e}`*")

    @caps.command(name="remove", description="Disable caps filtering")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def caps_remove(self, ctx: "PushieContext") -> None:
        """Disable excessive caps filtering."""
        assert ctx.guild is not None
        # Caps filtering is not natively supported by Discord AutoMod
        await ctx.info(
            "*Discord AutoMod doesn't support native caps filtering. Caps filtering not available.*"
        )

    # =========================================================================
    # FILTER MANAGEMENT
    # =========================================================================

    @commands.hybrid_command(
        name="filters reset", aliases=["filter-reset"], description="Reset all filters"
    )
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def filters_reset(self, ctx: "PushieContext") -> None:
        """Reset all message filters to default."""
        assert ctx.guild is not None
        try:
            rules = await ctx.guild.fetch_automod_rules()
            filter_rules = [
                r
                for r in rules
                if r.name
                in ("link_filter", "word_filter", "mention_filter", "caps_filter")
            ]

            if not filter_rules:
                await ctx.info("*No filter rules to reset.*")
                return

            for rule in filter_rules:
                await rule.delete()

            await ctx.ok(
                f"`{Emoji.RESET}` *All {len(filter_rules)} filter(s) have been reset.*"
            )
        except discord.Forbidden:
            await ctx.err("*I don't have permission to manage automod rules.*")
        except discord.HTTPException as e:
            await ctx.err(f"*Failed to reset filters: `{e}`*")

    # =========================================================================
    # ERROR HANDLING
    # =========================================================================

    async def cog_command_error(self, ctx: commands.Context, error: Exception) -> None:
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
        else:
            raise error


async def setup(bot: "Pushie") -> None:
    await bot.add_cog(Filters(bot))
