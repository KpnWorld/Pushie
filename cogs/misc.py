from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, cast

import discord
from discord.ext import commands

from emojis import Emoji
from ui import UI

if TYPE_CHECKING:
    from main import Pushie, PushieContext

log = logging.getLogger(__name__)


class Misc(commands.Cog, name="Miscellaneous"):
    """Autoresponders, reaction roles, embed builder, and polls."""

    def __init__(self, bot: "Pushie") -> None:
        self.bot = bot

    # =========================================================================
    # AUTORESPONDERS
    # =========================================================================

    @commands.hybrid_group(
        name="autoresponder",
        aliases=["autoreply", "autoresponse"],
        description="Manage automatic message responses",
    )
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def autoresponder(self, ctx: "PushieContext") -> None:
        """Autoresponder management commands."""
        pass

    @autoresponder.command(name="add", description="Add an autoresponder")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def autoresponder_add(
        self,
        ctx: "PushieContext",
        trigger: str,
        *,
        message: str,
    ) -> None:
        """Create an automatic response to a trigger word/phrase."""
        if ctx.guild is None:
            return
        g = ctx.bot.storage.get_guild_sync(ctx.guild.id)
        if not g:
            await ctx.err("*Guild data not initialized.*")
            return

        if trigger.lower() in g.autoresponders:
            await ctx.err(f"*Autoresponder for `{trigger}` already exists.*")
            return

        g.autoresponders[trigger.lower()] = {
            "response": message,
            "exact": False,
            "created_by": ctx.author.id,
            "created_at": str(ctx.message.created_at)
        }
        await ctx.bot.storage.save_guild(g)

        await ctx.ok(
            f"`{Emoji.INFO}` *Autoresponder added:* `{trigger}` → *{message[:50]}...*"
        )

    @autoresponder.command(name="remove", description="Remove an autoresponder")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def autoresponder_remove(self, ctx: "PushieContext", trigger: str) -> None:
        """Delete an autoresponder."""
        if ctx.guild is None:
            return
        g = ctx.bot.storage.get_guild_sync(ctx.guild.id)
        if not g:
            await ctx.err("*Guild data not initialized.*")
            return

        if trigger.lower() not in g.autoresponders:
            await ctx.err(f"*No autoresponder found for `{trigger}`.*")
            return

        del g.autoresponders[trigger.lower()]
        await ctx.bot.storage.save_guild(g)
        await ctx.ok(f"`{Emoji.INFO}` *Autoresponder for `{trigger}` deleted.*")

    @autoresponder.command(name="list", description="List all autoresponders")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def autoresponder_list(self, ctx: "PushieContext") -> None:
        """View all autoresponders in the server."""
        if ctx.guild is None:
            return
        g = ctx.bot.storage.get_guild_sync(ctx.guild.id)
        if not g or not g.autoresponders:
            await ctx.info("*No autoresponders configured.*")
            return

        triggers = list(g.autoresponders.keys())
        resp_text = "\n".join(f"> `{i+1}.` `{t}`" for i, t in enumerate(triggers[:10]))
        extra = f"\n> *+{len(triggers) - 10} more...*" if len(triggers) > 10 else ""

        embed = discord.Embed(
            description=f"`{Emoji.INFO}` *Autoresponders ({len(triggers)} total)*\n\n{resp_text}{extra}",
            color=0xFAB9EC
        )
        await ctx.send(embed=embed)

    @autoresponder.command(name="edit", description="Edit an autoresponder message")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def autoresponder_edit(
        self,
        ctx: "PushieContext",
        trigger: str,
        *,
        new_message: str,
    ) -> None:
        """Edit an existing autoresponder's message."""
        if ctx.guild is None:
            return
        g = ctx.bot.storage.get_guild_sync(ctx.guild.id)
        if not g:
            await ctx.err("*Guild data not initialized.*")
            return

        if trigger.lower() not in g.autoresponders:
            await ctx.err(f"*No autoresponder found for `{trigger}`.*")
            return

        g.autoresponders[trigger.lower()]["response"] = new_message
        await ctx.bot.storage.save_guild(g)
        await ctx.ok(f"`{Emoji.INFO}` *Autoresponder `{trigger}` updated.*")

    # =========================================================================
    # REACTION ROLES
    # =========================================================================

    @commands.hybrid_group(
        name="reactionrole",
        aliases=["rr", "reactrole"],
        description="Manage reaction role bindings",
    )
    @commands.guild_only()
    @commands.has_guild_permissions(manage_roles=True)
    async def reactionrole(self, ctx: "PushieContext") -> None:
        """Reaction role management commands."""
        pass

    @reactionrole.command(name="add", description="Bind an emoji to a role")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_roles=True)
    async def reactionrole_add(
        self,
        ctx: "PushieContext",
        emoji: str,
        role: discord.Role,
    ) -> None:
        """Bind an emoji to a role for reaction roles."""
        try:
            # Validate emoji
            await ctx.message.add_reaction(emoji)
            await ctx.message.remove_reaction(emoji, ctx.me)
        except discord.HTTPException:
            await ctx.err("*Invalid emoji.*")
            return

        author = cast(discord.Member, ctx.author)
        
        if role >= author.top_role:
            await ctx.err("*You cannot assign a role higher than your own.*")
            return

        # TODO: Store emoji → role binding in guild config
        await ctx.ok(f"`{Emoji.ROLE}` *{emoji} → {role.mention} reaction role added.*")

    @reactionrole.command(name="remove", description="Remove a reaction role binding")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_roles=True)
    async def reactionrole_remove(self, ctx: "PushieContext", emoji: str) -> None:
        """Remove a reaction role binding."""
        # TODO: Remove from guild config
        await ctx.ok(f"`{Emoji.ROLE}` *Reaction role {emoji} removed.*")

    @reactionrole.command(name="list", description="List all reaction role bindings")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_roles=True)
    async def reactionrole_list(self, ctx: "PushieContext") -> None:
        """View all reaction role bindings in the server."""
        # TODO: Fetch from guild config
        await ctx.info("*No reaction roles configured.*")

    @reactionrole.command(name="message", description="Set the reaction role message")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_roles=True)
    async def reactionrole_message(
        self, ctx: "PushieContext", message_link: str | None = None
    ) -> None:
        """Set or view which message reaction roles are attached to."""
        if message_link:
            # TODO: Parse link and set as reaction role message
            await ctx.ok(f"`{Emoji.ROLE}` *Reaction role message set.*")
        else:
            # TODO: Show current reaction role message
            await ctx.info("*No reaction role message set.*")

    # =========================================================================
    # EMBED CREATION
    # =========================================================================

    @commands.hybrid_command(
        name="embed", description="Create a custom embed from JSON"
    )
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def embed(self, ctx: "PushieContext", *, json_str: str) -> None:
        """Create a custom embed from JSON data."""
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            await ctx.err(f"*Invalid JSON: `{e}`*")
            return

        try:
            # Build embed from JSON
            embed = discord.Embed.from_dict(data)
            embed.color = embed.color or discord.Color(0xFAB9EC)
            await ctx.send(embed=embed)
        except (KeyError, ValueError) as e:
            await ctx.err(f"*Invalid embed data: `{e}`*")

    # =========================================================================
    # POLLS
    # =========================================================================

    @commands.hybrid_command(name="poll", description="Create a reaction-based poll")
    @commands.guild_only()
    async def poll(
        self,
        ctx: "PushieContext",
        question: str,
        *,
        options: str,
    ) -> None:
        """Create a poll with emoji reactions.

        Usage: `!poll "Should we add X feature?" "Yes|No|Maybe"`
        """
        # Parse options (comma or pipe separated)
        option_list = [opt.strip() for opt in options.replace("|", ",").split(",")]
        if len(option_list) < 2 or len(option_list) > 10:
            await ctx.err("*Poll must have between 2 and 10 options.*")
            return

        # Use regional indicator emojis (🇦 🇧 🇨 etc.)
        regional_indicators = ["🇦", "🇧", "🇨", "🇩", "🇪", "🇫", "🇬", "🇭", "🇮", "🇯"]
        emoji_list = regional_indicators[: len(option_list)]

        # Build poll embed
        description = f"**{question}**\n\n"
        for emoji, option in zip(emoji_list, option_list):
            description += f"{emoji} — {option}\n"

        embed = discord.Embed(
            description=description,
            color=0xFAB9EC,
        )
        embed.set_footer(text=f"Poll by {ctx.author.display_name}")

        poll_message = await ctx.send(embed=embed)

        # Add reactions
        for emoji in emoji_list:
            try:
                await poll_message.add_reaction(emoji)
            except discord.HTTPException:
                pass

    # =========================================================================
    # HELP COMMAND FOR MISC
    # =========================================================================

    @commands.hybrid_command(name="mischelp", description="Show misc commands help")
    async def mischelp(self, ctx: "PushieContext") -> None:
        """View help for miscellaneous commands."""
        embed = discord.Embed(
            title="Miscellaneous Commands",
            description=(
                f"`{Emoji.WHITELIST}` **Autoresponders** — Auto-reply to triggers\n"
                f"`{Emoji.ROLE}` **Reaction Roles** — Emoji roles system\n"
                f"`{Emoji.EMBED}` **Embed Creator** — Custom embeds from JSON\n"
                f"`{Emoji.INFO}` **Polls** — Create reaction polls\n"
            ),
            color=0xFAB9EC,
        )
        embed.add_field(
            name="Autoresponder",
            value=(
                "`!autoresponder add <trigger> <message>`\n"
                "`!autoresponder remove <trigger>`\n"
                "`!autoresponder list`\n"
                "`!autoresponder edit <trigger> <new_message>`"
            ),
            inline=False,
        )
        embed.add_field(
            name="Reaction Roles",
            value=(
                "`!reactionrole add <emoji> <role>`\n"
                "`!reactionrole remove <emoji>`\n"
                "`!reactionrole list`\n"
                "`!reactionrole message <link>`"
            ),
            inline=False,
        )
        embed.add_field(
            name="Other",
            value=("`!embed <json>`\n" '`!poll "Question?" "Option1|Option2|Option3"`'),
            inline=False,
        )

        await ctx.send(embed=embed)

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
    await bot.add_cog(Misc(bot))
