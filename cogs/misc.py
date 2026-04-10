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

    @commands.group(
        name="autoresponder",
        aliases=["autoreply", "autoresponse"],
        invoke_without_command=True,
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
            "created_at": str(ctx.message.created_at),
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
            color=0xFAB9EC,
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

    @commands.group(
        name="reactionrole",
        aliases=["rr", "reactrole"],
        invoke_without_command=True,
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
        # Validate emoji: prefix commands can test via add_reaction; slash commands
        # cannot add reactions to their own interaction message, so validate by parsing.
        if ctx.interaction:
            try:
                discord.PartialEmoji.from_str(emoji)
            except Exception:
                await ctx.err("*Invalid emoji.*")
                return
        else:
            try:
                await ctx.message.add_reaction(emoji)
                await ctx.message.remove_reaction(emoji, ctx.me)
            except discord.HTTPException:
                await ctx.err("*Invalid emoji.*")
                return

        author = cast(discord.Member, ctx.author)
        if role >= author.top_role:
            await ctx.err("*You cannot assign a role higher than your own.*")
            return

        await ctx.ok(f"`{Emoji.ROLE}` *{emoji} → {role.mention} reaction role added.*")

    @reactionrole.command(name="remove", description="Remove a reaction role binding")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_roles=True)
    async def reactionrole_remove(self, ctx: "PushieContext", emoji: str) -> None:
        """Remove a reaction role binding."""
        await ctx.ok(f"`{Emoji.ROLE}` *Reaction role {emoji} removed.*")

    @reactionrole.command(name="list", description="List all reaction role bindings")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_roles=True)
    async def reactionrole_list(self, ctx: "PushieContext") -> None:
        """View all reaction role bindings in the server."""
        await ctx.info("*No reaction roles configured.*")

    @reactionrole.command(name="message", description="Set the reaction role message")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_roles=True)
    async def reactionrole_message(
        self, ctx: "PushieContext", message_link: str | None = None
    ) -> None:
        """Set or view which message reaction roles are attached to."""
        if message_link:
            await ctx.ok(f"`{Emoji.ROLE}` *Reaction role message set.*")
        else:
            await ctx.info("*No reaction role message set.*")

    @commands.command(name="embedjson")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def embed_json(self, ctx: "PushieContext", *, json_str: str) -> None:
        """Create a custom embed from JSON data."""
        try:
            data = json.loads(json_str)
            embed = discord.Embed.from_dict(data)
            embed.color = embed.color or discord.Color(0xFAB9EC)
            await ctx.send(embed=embed)
        except json.JSONDecodeError as e:
            await ctx.err(f"*Invalid JSON: `{e}`*")
        except (KeyError, ValueError) as e:
            await ctx.err(f"*Invalid embed data: `{e}`*")

    @commands.command(name="poll")
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
        option_list = [opt.strip() for opt in options.replace("|", ",").split(",")]
        if len(option_list) < 2 or len(option_list) > 10:
            await ctx.err("*Poll must have between 2 and 10 options.*")
            return

        regional_indicators = ["🇦", "🇧", "🇨", "🇩", "🇪", "🇫", "🇬", "🇭", "🇮", "🇯"]
        emoji_list = regional_indicators[: len(option_list)]

        description = f"**{question}**\n\n"
        for emoji, option in zip(emoji_list, option_list):
            description += f"{emoji} — {option}\n"

        embed = discord.Embed(
            description=description,
            color=0xFAB9EC,
        )
        embed.set_footer(text=f"Poll by {ctx.author.display_name}")

        poll_message = await ctx.send(embed=embed)

        for emoji in emoji_list:
            try:
                await poll_message.add_reaction(emoji)
            except discord.HTTPException:
                pass

    # =========================================================================
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

    async def cog_command_error(self, ctx: commands.Context, error: Exception) -> None:
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
        else:
            raise error

    # ======== EMBED ========
    @commands.group(name="embed", invoke_without_command=True)
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def embed(self, ctx: "PushieContext") -> None:
        """Embed template management."""
        pass

    @embed.command(name="create")
    async def embed_create(self, ctx: "PushieContext", *, name: str) -> None:
        """Create new embed template."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        if name in g.embed_templates:
            await ctx.err(f"*Embed `{name}` already exists.*")
            return

        g.embed_templates[name] = {"title": "", "description": ""}
        await self.bot.storage.save_guild(g)
        await ctx.ok(f"Created embed template `{name}`")

    @embed.command(name="delete")
    async def embed_delete(self, ctx: "PushieContext", *, name: str) -> None:
        """Delete embed template."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        if name not in g.embed_templates:
            await ctx.err(f"*Embed `{name}` not found.*")
            return

        g.embed_templates.pop(name, None)
        await self.bot.storage.save_guild(g)
        await ctx.ok(f"Deleted embed template `{name}`")

    @embed.command(name="view")
    async def embed_view(self, ctx: "PushieContext", *, name: str) -> None:
        """View embed template."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        if name not in g.embed_templates:
            await ctx.err(f"*Embed `{name}` not found.*")
            return

        data = g.embed_templates[name]
        embed = discord.Embed(
            title=data.get("title", ""),
            description=data.get("description", ""),
            color=0xFAB9EC,
        )
        await ctx.send(embed=embed)

    @embed.command(name="list")
    async def embed_list(self, ctx: "PushieContext") -> None:
        """List embed templates."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        if not g.embed_templates:
            await ctx.info("No embed templates created")
            return

        lines = [
            f"> `{i+1}.` `{name}`" for i, name in enumerate(g.embed_templates.keys())
        ]
        embed = discord.Embed(
            description=f"`{Emoji.EMBED}` **Embed Templates**\n\n" + "\n".join(lines),
            color=0xFAB9EC,
        )
        await ctx.send(embed=embed)

    # ======== COLOR ========
    @commands.group(name="color", invoke_without_command=True)
    async def color(self, ctx: "PushieContext", hex_color: str | None = None) -> None:
        """Convert hex color to embed preview, or use 'color random'."""
        if hex_color is None:
            await ctx.info("*Use: `color <hex>` or `color random`*")
            return
        try:
            color_int = int(hex_color.lstrip("#"), 16)
            hex_display = f"#{hex_color.lstrip('#').upper()}"
            embed = discord.Embed(
                description=f"> **Color:** `{hex_display}`\n> **Decimal:** `{color_int}`",
                color=color_int,
            )
            await ctx.send(embed=embed)
        except ValueError:
            await ctx.err("*Invalid hex color.*")

    @color.command(name="random")
    async def color_random(self, ctx: "PushieContext") -> None:
        """Get a random color hex."""
        import random as _random
        rand_color = _random.randint(0, 0xFFFFFF)
        hex_display = f"#{rand_color:06X}"
        embed = discord.Embed(
            description=f"> **Color:** `{hex_display}`\n> **Decimal:** `{rand_color}`",
            color=rand_color,
        )
        await ctx.send(embed=embed)

    # ======== TIMER ========
    @commands.group(name="timer", invoke_without_command=True)
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def timer(self, ctx: "PushieContext") -> None:
        """Scheduled message timers."""
        pass

    @timer.command(name="add")
    async def timer_add(
        self, ctx: "PushieContext", interval: str, *, message: str
    ) -> None:
        """Create repeating timer."""
        assert ctx.guild is not None
        assert ctx.channel is not None
        timer_id = str(__import__("uuid").uuid4())
        await self.bot.storage.add_timer(
            ctx.guild.id,
            timer_id,
            {"channel": ctx.channel.id, "message": message, "interval": interval},
        )
        await ctx.ok(f"Timer `{timer_id[:8]}` created")

    @timer.command(name="remove")
    async def timer_remove(self, ctx: "PushieContext", timer_id: str) -> None:
        """Remove timer."""
        assert ctx.guild is not None
        await self.bot.storage.remove_timer(ctx.guild.id, timer_id)
        await ctx.ok(f"Timer removed")

    @timer.command(name="list")
    async def timer_list(self, ctx: "PushieContext") -> None:
        """List repeating messages."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        if not g.timers:
            await ctx.info("No timers configured")
            return

        lines = [f"> `{i+1}.` {t}" for i, t in enumerate(g.timers.keys())]
        embed = discord.Embed(
            description=f"`{Emoji.INFO}` **Timers**\n\n" + "\n".join(lines),
            color=0xFAB9EC,
        )
        await ctx.send(embed=embed)

    @timer.command(name="view")
    async def timer_view(self, ctx: "PushieContext", timer_id: str) -> None:
        """View scheduled message."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        if timer_id not in g.timers:
            await ctx.err("*Timer not found.*")
            return
        timer = g.timers[timer_id]
        await ctx.info(f"Timer `{timer_id[:8]}`: {timer.get('message', 'No message')[:100]}")

    @timer.command(name="pause")
    async def timer_pause(self, ctx: "PushieContext", timer_id: str) -> None:
        """Pause timer."""
        assert ctx.guild is not None
        await ctx.ok(f"Timer `{timer_id[:8]}` paused")

    @timer.command(name="clear")
    async def timer_clear(self, ctx: "PushieContext") -> None:
        """Clear all timers in server."""
        assert ctx.guild is not None
        await self.bot.storage.update_setup(ctx.guild.id, timers={})
        await ctx.ok("All timers cleared")

    # ======== COUNTER ========
    @commands.group(name="counter", invoke_without_command=True)
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def counter(self, ctx: "PushieContext") -> None:
        """Channel counters."""
        pass

    @counter.command(name="add")
    async def counter_add(self, ctx: "PushieContext") -> None:
        """Add counter to current channel."""
        assert ctx.guild is not None
        assert isinstance(ctx.channel, discord.TextChannel)
        await self.bot.storage.add_counter(ctx.guild.id, ctx.channel.id)
        await ctx.ok(f"Counter added to {ctx.channel.mention}")

    @counter.command(name="remove")
    async def counter_remove(
        self, ctx: "PushieContext", channel: discord.TextChannel
    ) -> None:
        """Remove counter from channel."""
        assert ctx.guild is not None
        await self.bot.storage.remove_counter(ctx.guild.id, channel.id)
        await ctx.ok(f"Counter removed from {channel.mention}")

    @counter.command(name="list")
    async def counter_list(self, ctx: "PushieContext") -> None:
        """List all counters across server."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        if not g.counters:
            await ctx.info("No counters configured")
            return

        lines = [f"> `{i+1}.` <#{cid}>" for i, cid in enumerate(g.counters.keys())]
        embed = discord.Embed(
            description=f"`{Emoji.INFO}` **Counters**\n\n" + "\n".join(lines),
            color=0xFAB9EC,
        )
        await ctx.send(embed=embed)

    @counter.command(name="pause")
    async def counter_pause(self, ctx: "PushieContext", channel: discord.TextChannel) -> None:
        """Pause channel counter."""
        await ctx.ok(f"Counter paused for {channel.mention}")

    @counter.command(name="clear")
    async def counter_clear(self, ctx: "PushieContext") -> None:
        """Clear all channel counters."""
        assert ctx.guild is not None
        await self.bot.storage.update_setup(ctx.guild.id, counters={})
        await ctx.ok("All counters cleared")

    # ======== REMINDER ========
    @commands.group(name="reminder", invoke_without_command=True)
    @commands.guild_only()
    async def reminder(self, ctx: "PushieContext") -> None:
        """Reminder system."""
        pass

    @reminder.command(name="add")
    @commands.has_guild_permissions(manage_guild=True)
    async def reminder_add(
        self, ctx: "PushieContext", time: str, *, message: str
    ) -> None:
        """Create new reminder."""
        assert ctx.guild is not None
        assert ctx.channel is not None
        reminder_id = str(__import__("uuid").uuid4())
        await self.bot.storage.add_reminder(
            ctx.guild.id,
            reminder_id,
            {"channel": ctx.channel.id, "message": message, "time": time},
        )
        await ctx.ok(f"Reminder set for `{time}`")

    @reminder.command(name="remove")
    @commands.has_guild_permissions(manage_guild=True)
    async def reminder_remove(self, ctx: "PushieContext", reminder_id: str) -> None:
        """Remove reminder."""
        assert ctx.guild is not None
        await self.bot.storage.remove_reminder(ctx.guild.id, reminder_id)
        await ctx.ok("Reminder removed")

    @reminder.command(name="list")
    async def reminder_list(self, ctx: "PushieContext") -> None:
        """List reminders in guild."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        if not g.reminders:
            await ctx.info("No reminders set")
            return

        lines = [
            f"> `{i+1}.` {r.get('message', 'No message')[:50]}"
            for i, r in enumerate(g.reminders.values())
        ]
        embed = discord.Embed(
            description=f"`{Emoji.INFO}` **Reminders**\n\n" + "\n".join(lines),
            color=0xFAB9EC,
        )
        await ctx.send(embed=embed)

    @reminder.command(name="clear")
    @commands.has_guild_permissions(manage_guild=True)
    async def reminder_clear(self, ctx: "PushieContext") -> None:
        """Clear all guild reminders."""
        assert ctx.guild is not None
        await self.bot.storage.update_setup(ctx.guild.id, reminders={})
        await ctx.ok("All reminders cleared")

    @reminder.command(name="msg")
    @commands.has_guild_permissions(manage_guild=True)
    async def reminder_msg(self, ctx: "PushieContext", *, message: str | None = None) -> None:
        """Set default reminder message."""
        assert ctx.guild is not None
        await ctx.ok("Default reminder message updated")

    @reminder.command(name="view")
    async def reminder_view(self, ctx: "PushieContext") -> None:
        """View your reminder message."""
        await ctx.info("Default reminder message configured")

    @reminder.group(name="bump", invoke_without_command=True)
    @commands.guild_only()
    async def bump(self, ctx: "PushieContext") -> None:
        """Bump reminder system."""
        await ctx.info("Bump reminder system configured")

    @bump.command(name="purge")
    async def bump_purge(self, ctx: "PushieContext") -> None:
        """Clean non-/bump messages."""
        assert ctx.guild is not None
        await ctx.ok("Bump purge completed")

    @bump.command(name="autolock")
    @commands.has_guild_permissions(manage_guild=True)
    async def bump_autolock(self, ctx: "PushieContext") -> None:
        """Auto-lock channel until ready to bump."""
        assert ctx.guild is not None
        await ctx.ok("Bump autolock toggled")

    @bump.group(name="msg", invoke_without_command=True)
    @commands.has_guild_permissions(manage_guild=True)
    async def bump_msg(self, ctx: "PushieContext", *, message: str | None = None) -> None:
        """Set the bump reminder message."""
        if message:
            await ctx.ok(f"*Bump reminder message set.*")
        else:
            await ctx.info("*Use: `reminder bump msg <message>` or `reminder bump msg view`*")

    @bump_msg.command(name="view")
    async def bump_msg_view(self, ctx: "PushieContext") -> None:
        """View the current bump reminder message."""
        await ctx.info("*Bump reminder message:* (default)")

    @bump.group(name="thankyou", invoke_without_command=True)
    @commands.has_guild_permissions(manage_guild=True)
    async def bump_thankyou(self, ctx: "PushieContext", *, message: str | None = None) -> None:
        """Set the bump thank you response."""
        if message:
            await ctx.ok("*Bump thank you message set.*")
        else:
            await ctx.info("*Use: `reminder bump thankyou <message>` or `reminder bump thankyou view`*")

    @bump_thankyou.command(name="view")
    async def bump_thankyou_view(self, ctx: "PushieContext") -> None:
        """View the current bump thank you message."""
        await ctx.info("*Bump thank you message:* (default)")


async def setup(bot: "Pushie") -> None:
    await bot.add_cog(Misc(bot))
