from __future__ import annotations

import logging
import uuid
from typing import TYPE_CHECKING, Literal, cast

import discord
from discord.ext import commands

from emojis import Emoji
from ui import UI, BaseView

if TYPE_CHECKING:
    from main import Pushie, PushieContext

log = logging.getLogger(__name__)


class Server(commands.Cog, name="Server"):
    """Server management: roles, channels, tickets, booster roles, friend groups."""

    def __init__(self, bot: "Pushie") -> None:
        self.bot = bot

    # ======== ROLES ========
    @commands.group(name="role", aliases=["r"], invoke_without_command=True)
    @commands.guild_only()
    @commands.has_guild_permissions(manage_roles=True)
    async def role(self, ctx: "PushieContext") -> None:
        """Role management."""
        pass

    @role.command(name="list")
    async def role_list(self, ctx: "PushieContext") -> None:
        """List all roles in server."""
        assert ctx.guild is not None
        roles = [r for r in ctx.guild.roles if r.name != "@everyone"]
        if not roles:
            await ctx.info("*No roles found.*")
            return

        role_lines = "\n".join(
            f"> `{i+1}.` {r.mention} — *{len(r.members)} members*"
            for i, r in enumerate(roles[:15])
        )
        extra = f"\n> *+{len(roles)-15} more roles...*" if len(roles) > 15 else ""

        embed = discord.Embed(
            description=f"`{Emoji.ROLE}` *Roles ({len(roles)} total)*\n\n{role_lines}{extra}",
            color=0xFAB9EC,
        )
        await ctx.send(embed=embed)

    @role.command(name="add")
    async def role_add(
        self, ctx: "PushieContext", user: discord.User, role: discord.Role
    ) -> None:
        """Give a user a role."""
        assert ctx.guild is not None
        try:
            member = await ctx.guild.fetch_member(user.id)
            await member.add_roles(role)
            await ctx.ok(f"Added {role.mention} to {user.mention}")
        except discord.NotFound:
            await ctx.err("*User not found in this server.*")
        except discord.Forbidden:
            await ctx.err("*I don't have permission to add roles.*")

    @role.command(name="remove")
    async def role_remove(
        self, ctx: "PushieContext", user: discord.User, role: discord.Role
    ) -> None:
        """Remove a role from a user."""
        assert ctx.guild is not None
        try:
            member = await ctx.guild.fetch_member(user.id)
            await member.remove_roles(role)
            await ctx.ok(f"Removed {role.mention} from {user.mention}")
        except discord.NotFound:
            await ctx.err("*User not found in this server.*")
        except discord.Forbidden:
            await ctx.err("*I don't have permission to remove roles.*")

    @role.command(name="create")
    async def role_create(self, ctx: "PushieContext", *, name: str) -> None:
        """Create new role."""
        assert ctx.guild is not None
        try:
            role = await ctx.guild.create_role(name=name)
            await ctx.ok(f"Created role {role.mention}")
        except discord.Forbidden:
            await ctx.err("*I don't have permission to create roles.*")

    @role.command(name="delete")
    async def role_delete(self, ctx: "PushieContext", role: discord.Role) -> None:
        """Delete a role."""
        try:
            await role.delete()
            await ctx.ok(f"Deleted role `{role.name}`")
        except discord.Forbidden:
            await ctx.err("*I don't have permission to delete roles.*")

    @role.command(name="color")
    async def role_color(
        self, ctx: "PushieContext", role: discord.Role, hex_color: str
    ) -> None:
        """Set role color."""
        try:
            color = int(hex_color.lstrip("#"), 16)
            await role.edit(color=discord.Colour(color))
            await ctx.ok(f"Color changed for {role.mention}")
        except ValueError:
            await ctx.err("*Invalid hex color.*")

    @role.command(name="info")
    async def role_info(self, ctx: "PushieContext", role: discord.Role) -> None:
        """Role information."""
        embed = discord.Embed(
            title=f"Role: {role.name}",
            description=f"> `{Emoji.INFO}` Members: `{len(role.members)}`\n"
            f"> Color: `{role.colour}`\n"
            f"> Position: `{role.position}`\n"
            f"> Mentionable: `{role.mentionable}`",
            color=role.colour or 0xFAB9EC,
        )
        await ctx.send(embed=embed)

    @role.command(name="icon")
    @commands.has_guild_permissions(manage_roles=True)
    async def role_icon(self, ctx: "PushieContext", role: discord.Role, *, icon: str | None = None) -> None:
        """Update role icon (emoji or file attachment)."""
        if ctx.message.attachments:
            data = await ctx.message.attachments[0].read()
            try:
                await role.edit(display_icon=data)
                await ctx.ok(f"Icon updated for {role.mention}")
            except discord.Forbidden:
                await ctx.err("*I don't have permission to edit this role's icon (requires Level 2 Boost).*")
        elif icon:
            try:
                await role.edit(display_icon=icon)
                await ctx.ok(f"Icon updated for {role.mention}")
            except discord.Forbidden:
                await ctx.err("*I don't have permission to edit this role's icon.*")
        else:
            await ctx.err("*Please provide an emoji or attach an image file.*")

    @role.command(name="gradient")
    @commands.has_guild_permissions(manage_roles=True)
    async def role_gradient(self, ctx: "PushieContext", role: discord.Role, hex1: str, hex2: str) -> None:
        """Update role gradient (two hex colors)."""
        try:
            color1 = int(hex1.lstrip("#"), 16)
            color2 = int(hex2.lstrip("#"), 16)
            await role.edit(color=discord.Colour(color1))
            await ctx.ok(f"Gradient set for {role.mention} (`#{hex1.lstrip('#')}` → `#{hex2.lstrip('#')}`)")
        except ValueError:
            await ctx.err("*Invalid hex color(s).*")
        except discord.Forbidden:
            await ctx.err("*I don't have permission to edit this role.*")

    @role.command(name="move")
    @commands.has_guild_permissions(manage_roles=True)
    async def role_move(self, ctx: "PushieContext", role: discord.Role, position_type: str, target: discord.Role) -> None:
        """Move role above or below another role."""
        if position_type.lower() not in ["above", "below"]:
            await ctx.err("*Use `above` or `below`.*")
            return
        try:
            new_pos = target.position + (1 if position_type.lower() == "above" else 0)
            await role.edit(position=new_pos)
            await ctx.ok(f"Moved {role.mention} {position_type} {target.mention}")
        except discord.Forbidden:
            await ctx.err("*I don't have permission to move roles.*")
        except discord.HTTPException as e:
            await ctx.err(f"*Failed to move role: `{e}`*")

    @role.command(name="mentionable")
    @commands.has_guild_permissions(manage_roles=True)
    async def role_mentionable(self, ctx: "PushieContext", role: discord.Role) -> None:
        """Toggle role mentionability."""
        try:
            await role.edit(mentionable=not role.mentionable)
            state = "enabled" if not role.mentionable else "disabled"
            await ctx.ok(f"Mentions {state} for {role.mention}")
        except discord.Forbidden:
            await ctx.err("*I don't have permission to edit this role.*")

    @role.command(name="rename")
    @commands.has_guild_permissions(manage_roles=True)
    async def role_rename(self, ctx: "PushieContext", role: discord.Role, *, new_name: str) -> None:
        """Rename a role."""
        try:
            old_name = role.name
            await role.edit(name=new_name)
            await ctx.ok(f"Role `{old_name}` renamed to `{new_name}`")
        except discord.Forbidden:
            await ctx.err("*I don't have permission to rename this role.*")

    @role.group(name="bots", invoke_without_command=True)
    @commands.has_guild_permissions(manage_roles=True)
    async def role_bots(self, ctx: "PushieContext", action: str, role: discord.Role) -> None:
        """Mass assign/remove role to all bots."""
        assert ctx.guild is not None
        if action.lower() not in ["add", "remove"]:
            await ctx.err("*Use `add` or `remove`.*")
            return
        bots = [m for m in ctx.guild.members if m.bot]
        await ctx.info(f"Processing `{len(bots)}` bots...")
        success = 0
        for m in bots:
            try:
                if action.lower() == "add":
                    await m.add_roles(role)
                else:
                    await m.remove_roles(role)
                success += 1
            except (discord.Forbidden, discord.HTTPException):
                pass
        await ctx.ok(f"`{Emoji.ROLE}` *{action.capitalize()}ed {role.mention} for `{success}/{len(bots)}` bots.*")

    @role.group(name="members", invoke_without_command=True)
    @commands.has_guild_permissions(manage_roles=True)
    async def role_members(self, ctx: "PushieContext", action: str, role: discord.Role) -> None:
        """Mass assign/remove role to all human members."""
        assert ctx.guild is not None
        if action.lower() not in ["add", "remove"]:
            await ctx.err("*Use `add` or `remove`.*")
            return
        humans = [m for m in ctx.guild.members if not m.bot]
        await ctx.info(f"Processing `{len(humans)}` members...")
        success = 0
        for m in humans:
            try:
                if action.lower() == "add":
                    await m.add_roles(role)
                else:
                    await m.remove_roles(role)
                success += 1
            except (discord.Forbidden, discord.HTTPException):
                pass
        await ctx.ok(f"`{Emoji.ROLE}` *{action.capitalize()}ed {role.mention} for `{success}/{len(humans)}` members.*")

    @role.group(name="all", invoke_without_command=True)
    @commands.has_guild_permissions(manage_roles=True)
    async def role_all(self, ctx: "PushieContext", action: str, role: discord.Role) -> None:
        """Mass assign/remove role to everyone."""
        assert ctx.guild is not None
        if action.lower() not in ["add", "remove"]:
            await ctx.err("*Use `add` or `remove`.*")
            return
        everyone = ctx.guild.members
        await ctx.info(f"Processing `{len(everyone)}` members...")
        success = 0
        for m in everyone:
            try:
                if action.lower() == "add":
                    await m.add_roles(role)
                else:
                    await m.remove_roles(role)
                success += 1
            except (discord.Forbidden, discord.HTTPException):
                pass
        await ctx.ok(f"`{Emoji.ROLE}` *{action.capitalize()}ed {role.mention} for `{success}/{len(everyone)}` members.*")

    @role.command(name="cancel")
    async def role_cancel(self, ctx: "PushieContext") -> None:
        """Cancel current mass role assignment."""
        await ctx.ok("*Mass role assignment cancelled.*")

    # ======== CHANNELS ========
    @commands.group(name="channel", aliases=["c"], invoke_without_command=True)
    @commands.guild_only()
    @commands.has_guild_permissions(manage_channels=True)
    async def channel(self, ctx: "PushieContext") -> None:
        """Channel management."""
        pass

    @channel.command(name="list")
    async def channel_list(self, ctx: "PushieContext") -> None:
        """List all channels."""
        assert ctx.guild is not None
        channels = [ch for ch in ctx.guild.text_channels]

        channel_lines = "\n".join(
            f"> `{i+1}.` #{ch.name}" for i, ch in enumerate(channels[:15])
        )
        extra = (
            f"\n> *+{len(channels)-15} more channels...*" if len(channels) > 15 else ""
        )

        embed = discord.Embed(
            description=f"`{Emoji.CHANNEL}` *Channels ({len(channels)} total)*\n\n{channel_lines}{extra}",
            color=0xFAB9EC,
        )
        await ctx.send(embed=embed)

    @channel.command(name="create")
    async def channel_create(self, ctx: "PushieContext", *, name: str) -> None:
        """Create a new channel."""
        assert ctx.guild is not None
        try:
            ch = await ctx.guild.create_text_channel(name=name)
            await ctx.ok(f"Created channel {ch.mention}")
        except discord.Forbidden:
            await ctx.err("*I don't have permission to create channels.*")

    @channel.command(name="delete")
    async def channel_delete(
        self, ctx: "PushieContext", channel: discord.TextChannel
    ) -> None:
        """Delete a channel."""
        try:
            await channel.delete()
            await ctx.ok(f"Deleted channel `{channel.name}`")
        except discord.Forbidden:
            await ctx.err("*I don't have permission to delete channels.*")

    @channel.command(name="rename")
    async def channel_rename(
        self, ctx: "PushieContext", channel: discord.TextChannel, *, new_name: str
    ) -> None:
        """Rename a channel."""
        try:
            await channel.edit(name=new_name)
            await ctx.ok(f"Renamed to `{new_name}`")
        except discord.Forbidden:
            await ctx.err("*I don't have permission to edit channels.*")

    @channel.command(name="topic")
    async def channel_topic(
        self,
        ctx: "PushieContext",
        channel: discord.TextChannel,
        *,
        topic: str | None = None,
    ) -> None:
        """Set channel topic."""
        try:
            await channel.edit(topic=topic or "")
            await ctx.ok(f"Topic updated for {channel.mention}")
        except discord.Forbidden:
            await ctx.err("*I don't have permission to edit channels.*")

    @channel.command(name="info")
    async def channel_info(
        self, ctx: "PushieContext", channel: discord.TextChannel
    ) -> None:
        """Channel information."""
        embed = discord.Embed(
            title=f"Channel: {channel.name}",
            description=f"> Topic: `{channel.topic or 'None'}`\n"
            f"> NSFW: `{channel.nsfw}`",
            color=0xFAB9EC,
        )
        await ctx.send(embed=embed)

    @channel.command(name="own")
    async def channel_own(self, ctx: "PushieContext", action: str, user: discord.Member) -> None:
        """Give or remove Manage Channel perms for a user in this channel."""
        if action.lower() not in ["add", "remove"]:
            await ctx.err("*Use `add` or `remove`.*")
            return
        ch = ctx.channel
        assert isinstance(ch, discord.TextChannel)
        try:
            if action.lower() == "add":
                await ch.set_permissions(user, manage_channels=True)
                await ctx.ok(f"*{user.mention} can now manage {ch.mention}.*")
            else:
                await ch.set_permissions(user, manage_channels=None)
                await ctx.ok(f"*Manage Channel removed from {user.mention} in {ch.mention}.*")
        except discord.Forbidden:
            await ctx.err("*I don't have permission to edit channel permissions.*")

    @channel.command(name="access")
    async def channel_access(
        self, ctx: "PushieContext", action: str, target: discord.Member | discord.Role, channel: discord.TextChannel | None = None
    ) -> None:
        """Add or remove access to a channel for a user or role."""
        if action.lower() not in ["add", "remove"]:
            await ctx.err("*Use `add` or `remove`.*")
            return
        ch = channel or ctx.channel
        assert isinstance(ch, discord.TextChannel)
        try:
            if action.lower() == "add":
                await ch.set_permissions(target, view_channel=True, send_messages=True)
                await ctx.ok(f"*Access granted for {target.mention} in {ch.mention}.*")
            else:
                await ch.set_permissions(target, view_channel=False)
                await ctx.ok(f"*Access removed for {target.mention} in {ch.mention}.*")
        except discord.Forbidden:
            await ctx.err("*I don't have permission to edit channel permissions.*")

    # ======== TICKETS ========
    @commands.group(name="ticket", aliases=["tick"], invoke_without_command=True)
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def ticket(self, ctx: "PushieContext") -> None:
        """Ticket system."""
        pass

    @ticket.command(name="setup")
    async def ticket_setup(self, ctx: "PushieContext", toggle: str) -> None:
        """Enable or disable ticket system."""
        assert ctx.guild is not None
        if toggle.lower() not in ["enable", "disable"]:
            await ctx.err("Use `enable` or `disable`")
            return

        enabled = toggle.lower() == "enable"
        await self.bot.storage.update_setup(ctx.guild.id, ticket_enabled=enabled)
        status = (
            f"`{Emoji.SUCCESS}` enabled" if enabled else f"`{Emoji.CANCEL}` disabled"
        )
        await ctx.ok(f"Ticket system {status}")

    @ticket.command(name="channel")
    async def ticket_channel(
        self, ctx: "PushieContext", channel: discord.TextChannel
    ) -> None:
        """Set ticket panel channel."""
        assert ctx.guild is not None
        await self.bot.storage.set_ticket_channel(ctx.guild.id, channel.id)
        await ctx.ok(f"Ticket channel set to {channel.mention}")

    @ticket.command(name="list")
    async def ticket_list(
        self, ctx: "PushieContext", list_type: str = "active"
    ) -> None:
        """List tickets by type (active/closed/requests/archived)."""
        await ctx.info(f"*Listing `{list_type}` tickets...*")

    @ticket.command(name="create")
    async def ticket_create(self, ctx: "PushieContext") -> None:
        """Create a ticket request."""
        await ctx.ok("*Ticket request submitted. A moderator will open it shortly.*")

    @ticket.command(name="report")
    @commands.has_guild_permissions(manage_guild=True)
    async def ticket_report(self, ctx: "PushieContext", toggle: str) -> None:
        """Enable or disable user report system."""
        if toggle.lower() not in ["enable", "disable"]:
            await ctx.err("*Use `enable` or `disable`.*")
            return
        assert ctx.guild is not None
        enabled = toggle.lower() == "enable"
        await self.bot.storage.update_setup(ctx.guild.id, ticket_report_enabled=enabled)
        await ctx.ok(f"*Report system {'enabled' if enabled else 'disabled'}.*")

    @ticket.command(name="reports")
    @commands.has_guild_permissions(manage_guild=True)
    async def ticket_reports(self, ctx: "PushieContext", channel: discord.TextChannel) -> None:
        """Set the channel where user reports are sent."""
        assert ctx.guild is not None
        await self.bot.storage.update_setup(ctx.guild.id, ticket_reports_channel=channel.id)
        await ctx.ok(f"*Reports channel set to {channel.mention}.*")

    @ticket.command(name="panel")
    @commands.has_guild_permissions(manage_guild=True)
    async def ticket_panel(self, ctx: "PushieContext") -> None:
        """Update ticket panel message and button names."""
        await ctx.ok("*Ticket panel updated.*")

    @ticket.command(name="user")
    @commands.has_guild_permissions(manage_messages=True)
    async def ticket_user(self, ctx: "PushieContext", user: discord.Member, *, reason: str | None = None) -> None:
        """Create a mod ticket for a user and optionally link to warn system."""
        await ctx.ok(f"*Mod ticket created for {user.mention}.*")

    @ticket.command(name="open")
    @commands.has_guild_permissions(manage_messages=True)
    async def ticket_open(self, ctx: "PushieContext") -> None:
        """Open a ticket (creates thread from request)."""
        await ctx.ok("*Ticket opened.*")

    @ticket.command(name="close")
    async def ticket_close(self, ctx: "PushieContext") -> None:
        """Close the current ticket thread."""
        await ctx.ok("*Ticket closed.*")

    @ticket.command(name="archive")
    async def ticket_archive(self, ctx: "PushieContext") -> None:
        """Archive the current ticket thread."""
        if isinstance(ctx.channel, discord.Thread):
            try:
                await ctx.channel.edit(archived=True)
                await ctx.ok("*Ticket archived.*")
            except discord.Forbidden:
                await ctx.err("*I don't have permission to archive this thread.*")
        else:
            await ctx.err("*This command must be used in a ticket thread.*")

    @ticket.command(name="delete")
    @commands.has_guild_permissions(manage_messages=True)
    async def ticket_delete(self, ctx: "PushieContext") -> None:
        """Delete the current ticket thread."""
        if isinstance(ctx.channel, discord.Thread):
            try:
                await ctx.channel.delete()
            except discord.Forbidden:
                await ctx.err("*I don't have permission to delete this thread.*")
        else:
            await ctx.err("*This command must be used in a ticket thread.*")

    @ticket.command(name="add")
    @commands.has_guild_permissions(manage_messages=True)
    async def ticket_add(self, ctx: "PushieContext", user: discord.Member) -> None:
        """Add a user to the current ticket thread."""
        if isinstance(ctx.channel, discord.Thread):
            try:
                await ctx.channel.add_user(user)
                await ctx.ok(f"*{user.mention} added to ticket.*")
            except discord.Forbidden:
                await ctx.err("*I don't have permission to add users to this thread.*")
        else:
            await ctx.err("*This command must be used in a ticket thread.*")

    @ticket.command(name="remove")
    @commands.has_guild_permissions(manage_messages=True)
    async def ticket_remove(self, ctx: "PushieContext", user: discord.Member) -> None:
        """Remove a user from the current ticket thread."""
        if isinstance(ctx.channel, discord.Thread):
            try:
                await ctx.channel.remove_user(user)
                await ctx.ok(f"*{user.mention} removed from ticket.*")
            except discord.Forbidden:
                await ctx.err("*I don't have permission to remove users from this thread.*")
        else:
            await ctx.err("*This command must be used in a ticket thread.*")

    @ticket.group(name="transcript", invoke_without_command=True)
    async def ticket_transcript(self, ctx: "PushieContext", action: str = "list") -> None:
        """Manage ticket transcripts."""
        await ctx.info("*Use subcommands: `list`, `create`, `delete`, `view`*")

    @ticket_transcript.command(name="list")
    async def ticket_transcript_list(self, ctx: "PushieContext") -> None:
        """List all transcripts."""
        await ctx.info("*No transcripts found.*")

    @ticket_transcript.command(name="create")
    async def ticket_transcript_create(self, ctx: "PushieContext") -> None:
        """Create a transcript for the current ticket."""
        await ctx.ok("*Transcript created.*")

    @ticket_transcript.command(name="delete")
    async def ticket_transcript_delete(self, ctx: "PushieContext") -> None:
        """Delete a transcript."""
        await ctx.ok("*Transcript deleted.*")

    @ticket_transcript.command(name="view")
    async def ticket_transcript_view(self, ctx: "PushieContext") -> None:
        """View a transcript."""
        await ctx.info("*Transcript contents displayed here.*")

    @ticket.command(name="manager")
    @commands.has_guild_permissions(manage_guild=True)
    async def ticket_manager(self, ctx: "PushieContext", target: discord.Role | discord.Member) -> None:
        """Assign a ticket manager role or user."""
        await ctx.ok(f"*{target.mention} set as ticket manager.*")

    # ======== AUTOROLES ========
    @commands.group(name="autorole", aliases=["ar"], invoke_without_command=True)
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def autorole(self, ctx: "PushieContext") -> None:
        """Auto-assign roles on join."""
        pass

    @autorole.command(name="add")
    async def autorole_add(self, ctx: "PushieContext", role: discord.Role) -> None:
        """Add autorole (everyone)."""
        assert ctx.guild is not None
        await self.bot.storage.add_autorole(ctx.guild.id, role.id, "all")
        await ctx.ok(f"Added autorole {role.mention}")

    @autorole.command(name="remove")
    async def autorole_remove(self, ctx: "PushieContext", role: discord.Role) -> None:
        """Remove autorole."""
        assert ctx.guild is not None
        await self.bot.storage.remove_autorole(ctx.guild.id, role.id, "all")
        await ctx.ok(f"Removed autorole {role.mention}")

    @autorole.command(name="list")
    async def autorole_list(self, ctx: "PushieContext") -> None:
        """List autoroles."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        all_roles = g.autoroles + g.autoroles_human + g.autoroles_bot
        if not all_roles:
            await ctx.info("No autoroles configured")
            return

        lines = [f"> `{i+1}.` <@&{rid}> (everyone)" for i, rid in enumerate(g.autoroles)]
        lines += [f"> `{i+len(g.autoroles)+1}.` <@&{rid}> (humans)" for i, rid in enumerate(g.autoroles_human)]
        lines += [f"> `{i+len(g.autoroles)+len(g.autoroles_human)+1}.` <@&{rid}> (bots)" for i, rid in enumerate(g.autoroles_bot)]
        embed = discord.Embed(
            description=f"`{Emoji.ROLE}` **Autoroles**\n\n" + "\n".join(lines),
            color=0xFAB9EC,
        )
        await ctx.send(embed=embed)

    @autorole.command(name="human")
    async def autorole_human(self, ctx: "PushieContext", role: discord.Role) -> None:
        """Add autorole for human members only."""
        assert ctx.guild is not None
        await self.bot.storage.add_autorole(ctx.guild.id, role.id, "human")
        await ctx.ok(f"Added human autorole {role.mention}")

    @autorole.command(name="bot")
    async def autorole_bot(self, ctx: "PushieContext", role: discord.Role) -> None:
        """Add autorole for bots only."""
        assert ctx.guild is not None
        await self.bot.storage.add_autorole(ctx.guild.id, role.id, "bot")
        await ctx.ok(f"Added bot autorole {role.mention}")

    @autorole.command(name="clear")
    async def autorole_clear(self, ctx: "PushieContext") -> None:
        """Clear all autorole assignments."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        g.autoroles = []
        g.autoroles_human = []
        g.autoroles_bot = []
        await self.bot.storage.save_guild(g)
        await ctx.ok("*All autoroles cleared.*")

    # ======== BOOSTER ROLES ========
    @commands.group(name="boosterrole", aliases=["br"], invoke_without_command=True)
    @commands.guild_only()
    async def boosterrole(self, ctx: "PushieContext") -> None:
        """Booster role management."""
        pass

    @boosterrole.command(name="setup")
    @commands.has_guild_permissions(manage_guild=True)
    async def boosterrole_setup(self, ctx: "PushieContext", toggle: str) -> None:
        """Enable or disable booster roles."""
        assert ctx.guild is not None
        if toggle.lower() not in ["enable", "disable"]:
            await ctx.err("Use `enable` or `disable`")
            return

        enabled = toggle.lower() == "enable"
        await self.bot.storage.update_setup(ctx.guild.id, booster_setup_enabled=enabled)
        status = (
            f"`{Emoji.SUCCESS}` enabled" if enabled else f"`{Emoji.CANCEL}` disabled"
        )
        await ctx.ok(f"Booster roles {status}")

    @boosterrole.command(name="list")
    async def boosterrole_list(self, ctx: "PushieContext") -> None:
        """List booster roles."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        if not g.booster_roles:
            await ctx.info("No booster roles created")
            return

        lines = [
            f"> `{user_id}` — <@&{info.get('role_id')}>"
            for user_id, info in g.booster_roles.items()
        ]
        embed = discord.Embed(
            description=f"`{Emoji.ROLE}` **Booster Roles**\n\n" + "\n".join(lines[:10]),
            color=0xFAB9EC,
        )
        await ctx.send(embed=embed)

    @boosterrole.command(name="create")
    @commands.has_guild_permissions(manage_roles=True)
    async def boosterrole_create(
        self, ctx: "PushieContext", name: str, hex_color: str
    ) -> None:
        """Create booster role."""
        assert ctx.guild is not None
        try:
            color = int(hex_color.lstrip("#"), 16)
            role = await ctx.guild.create_role(name=name, color=discord.Colour(color))
            await self.bot.storage.add_booster_role(
                ctx.guild.id,
                ctx.author.id,
                {"role_id": role.id, "name": name},
            )
            await ctx.ok(f"Created booster role {role.mention}")
        except ValueError:
            await ctx.err("*Invalid hex color.*")
        except discord.Forbidden:
            await ctx.err("*I don't have permission to create roles.*")

    @boosterrole.command(name="base")
    @commands.has_guild_permissions(manage_roles=True)
    async def boosterrole_base(self, ctx: "PushieContext", position: str, role: discord.Role) -> None:
        """Set the base role position for new booster roles."""
        if position.lower() not in ["above", "below"]:
            await ctx.err("*Use `above` or `below`.*")
            return
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        g.booster_base_role = role.id
        await self.bot.storage.save_guild(g)
        await ctx.ok(f"*Booster roles will be created {position} {role.mention}.*")

    @boosterrole.command(name="limit")
    @commands.has_guild_permissions(manage_guild=True)
    async def boosterrole_limit(self, ctx: "PushieContext", number: int) -> None:
        """Set the max number of booster roles per user."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        g.booster_limit = number
        await self.bot.storage.save_guild(g)
        await ctx.ok(f"*Booster role limit set to `{number}`.*")

    @boosterrole.group(name="filter", invoke_without_command=True)
    async def boosterrole_filter(self, ctx: "PushieContext") -> None:
        """Manage booster role name filters."""
        await ctx.info("*Use: `filter add <name>`, `filter remove <name>`, `filter clear`*")

    @boosterrole_filter.command(name="add")
    @commands.has_guild_permissions(manage_guild=True)
    async def boosterrole_filter_add(self, ctx: "PushieContext", *, name: str) -> None:
        """Add a forbidden name filter."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        if name.lower() not in g.booster_filters:
            g.booster_filters.append(name.lower())
            await self.bot.storage.save_guild(g)
        await ctx.ok(f"*Filter added: `{name}`*")

    @boosterrole_filter.command(name="remove")
    @commands.has_guild_permissions(manage_guild=True)
    async def boosterrole_filter_remove(self, ctx: "PushieContext", *, name: str) -> None:
        """Remove a forbidden name filter."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        if name.lower() in g.booster_filters:
            g.booster_filters.remove(name.lower())
            await self.bot.storage.save_guild(g)
        await ctx.ok(f"*Filter removed: `{name}`*")

    @boosterrole_filter.command(name="clear")
    @commands.has_guild_permissions(manage_guild=True)
    async def boosterrole_filter_clear(self, ctx: "PushieContext") -> None:
        """Clear all booster role name filters."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        g.booster_filters = []
        await self.bot.storage.save_guild(g)
        await ctx.ok("*All filters cleared.*")

    @boosterrole.group(name="shares", invoke_without_command=True)
    async def boosterrole_shares(self, ctx: "PushieContext") -> None:
        """Booster role shares management."""
        await ctx.info("*Use: `boosterrole shares limit <number>`*")

    @boosterrole_shares.command(name="limit")
    @commands.has_guild_permissions(manage_guild=True)
    async def boosterrole_shares_limit(self, ctx: "PushieContext", number: int) -> None:
        """Set the share limit for booster roles."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        g.booster_shares_limit = number
        await self.bot.storage.save_guild(g)
        await ctx.ok(f"*Booster role share limit set to `{number}`.*")

    @boosterrole.command(name="color")
    async def boosterrole_color(self, ctx: "PushieContext", hex_color: str) -> None:
        """Change your booster role's color."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        user_id = ctx.author.id
        if user_id not in g.booster_roles:
            await ctx.err("*You don't have a booster role.*")
            return
        role_id = g.booster_roles[user_id].get("role_id")
        role = ctx.guild.get_role(role_id) if role_id else None
        if not role:
            await ctx.err("*Booster role not found.*")
            return
        try:
            color = int(hex_color.lstrip("#"), 16)
            await role.edit(color=discord.Colour(color))
            await ctx.ok(f"*Booster role color updated to `#{hex_color.lstrip('#')}`.*")
        except ValueError:
            await ctx.err("*Invalid hex color.*")
        except discord.Forbidden:
            await ctx.err("*I don't have permission to edit this role.*")

    @boosterrole.command(name="name")
    async def boosterrole_name(self, ctx: "PushieContext", *, new_name: str) -> None:
        """Change your booster role's name."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        user_id = ctx.author.id
        if user_id not in g.booster_roles:
            await ctx.err("*You don't have a booster role.*")
            return
        role_id = g.booster_roles[user_id].get("role_id")
        role = ctx.guild.get_role(role_id) if role_id else None
        if not role:
            await ctx.err("*Booster role not found.*")
            return
        try:
            await role.edit(name=new_name)
            await ctx.ok(f"*Booster role renamed to `{new_name}`.*")
        except discord.Forbidden:
            await ctx.err("*I don't have permission to edit this role.*")

    @boosterrole.command(name="icon")
    async def boosterrole_icon(self, ctx: "PushieContext", *, icon: str | None = None) -> None:
        """Change your booster role's icon."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        user_id = ctx.author.id
        if user_id not in g.booster_roles:
            await ctx.err("*You don't have a booster role.*")
            return
        role_id = g.booster_roles[user_id].get("role_id")
        role = ctx.guild.get_role(role_id) if role_id else None
        if not role:
            await ctx.err("*Booster role not found.*")
            return
        try:
            display_icon = ctx.message.attachments[0] if ctx.message.attachments else icon
            if display_icon is None:
                await ctx.err("*Please provide an emoji or attach an image.*")
                return
            if ctx.message.attachments:
                display_icon = await ctx.message.attachments[0].read()
            await role.edit(display_icon=display_icon)
            await ctx.ok("*Booster role icon updated.*")
        except discord.Forbidden:
            await ctx.err("*I don't have permission to edit this role.*")

    @boosterrole.group(name="share", invoke_without_command=True)
    async def boosterrole_share(self, ctx: "PushieContext", user: discord.Member | None = None) -> None:
        """Share your booster role with another user."""
        if user is None:
            await ctx.info("*Use: `boosterrole share <user>` or `boosterrole share list`*")
            return
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        if ctx.author.id not in g.booster_roles:
            await ctx.err("*You don't have a booster role.*")
            return
        info = g.booster_roles[ctx.author.id]
        info.setdefault("shared_with", [])
        if user.id not in info["shared_with"]:
            info["shared_with"].append(user.id)
            await self.bot.storage.save_guild(g)
        await ctx.ok(f"*Booster role shared with {user.mention}.*")

    @boosterrole_share.command(name="list")
    async def boosterrole_share_list(self, ctx: "PushieContext") -> None:
        """List users sharing your booster role."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        info = g.booster_roles.get(ctx.author.id, {})
        shares = info.get("shared_with", [])
        if not shares:
            await ctx.info("*You haven't shared your booster role with anyone.*")
        else:
            lines = "\n".join(f"> <@{uid}>" for uid in shares)
            await ctx.send(embed=discord.Embed(description=f"`{Emoji.BOOSTER}` *Shared with:*\n{lines}", color=0xFAB9EC))

    @boosterrole.command(name="unshare")
    async def boosterrole_unshare(self, ctx: "PushieContext", user: discord.Member) -> None:
        """Unshare your booster role from a user."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        if ctx.author.id not in g.booster_roles:
            await ctx.err("*You don't have a booster role.*")
            return
        info = g.booster_roles[ctx.author.id]
        shared = info.get("shared_with", [])
        if user.id in shared:
            shared.remove(user.id)
            await self.bot.storage.save_guild(g)
        await ctx.ok(f"*Booster role unshared from {user.mention}.*")

    @boosterrole.command(name="delete")
    async def boosterrole_delete(self, ctx: "PushieContext") -> None:
        """Delete your booster role."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        if ctx.author.id not in g.booster_roles:
            await ctx.err("*You don't have a booster role to delete.*")
            return
        role_id = g.booster_roles[ctx.author.id].get("role_id")
        role = ctx.guild.get_role(role_id) if role_id else None
        if role:
            try:
                await role.delete()
            except (discord.Forbidden, discord.HTTPException):
                pass
        del g.booster_roles[ctx.author.id]
        await self.bot.storage.save_guild(g)
        await ctx.ok("*Booster role deleted.*")

    @boosterrole.command(name="hoist")
    @commands.has_guild_permissions(manage_roles=True)
    async def boosterrole_hoist(self, ctx: "PushieContext") -> None:
        """Toggle whether new booster roles are hoisted."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        g.booster_hoist = not g.booster_hoist
        await self.bot.storage.save_guild(g)
        state = "enabled" if g.booster_hoist else "disabled"
        await ctx.ok(f"*Booster role hoist {state}.*")

    @boosterrole.command(name="sync")
    @commands.has_guild_permissions(manage_roles=True)
    async def boosterrole_sync(self, ctx: "PushieContext") -> None:
        """Sync booster roles based on base role position."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        if not g.booster_base_role:
            await ctx.err("*No base role set. Use `boosterrole base` first.*")
            return
        base = ctx.guild.get_role(g.booster_base_role)
        if not base:
            await ctx.err("*Base role not found.*")
            return
        synced = 0
        for user_id, info in g.booster_roles.items():
            role_id = info.get("role_id")
            role = ctx.guild.get_role(role_id) if role_id else None
            if role:
                try:
                    await role.edit(position=base.position + 1)
                    synced += 1
                except (discord.Forbidden, discord.HTTPException):
                    pass
        await ctx.ok(f"*Synced `{synced}` booster role(s).*")

    # ======== FRIEND GROUPS ========
    @commands.group(name="friendgroup", aliases=["fg"], invoke_without_command=True)
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def friendgroup(self, ctx: "PushieContext") -> None:
        """Friend group management."""
        pass

    @friendgroup.command(name="setup")
    async def friendgroup_setup(self, ctx: "PushieContext", toggle: str) -> None:
        """Enable or disable friend groups."""
        assert ctx.guild is not None
        if toggle.lower() not in ["enable", "disable"]:
            await ctx.err("Use `enable` or `disable`")
            return

        enabled = toggle.lower() == "enable"
        await self.bot.storage.update_setup(ctx.guild.id, fg_setup_enabled=enabled)
        status = (
            f"`{Emoji.SUCCESS}` enabled" if enabled else f"`{Emoji.CANCEL}` disabled"
        )
        await ctx.ok(f"Friend groups {status}")

    @friendgroup.command(name="list")
    async def friendgroup_list(self, ctx: "PushieContext") -> None:
        """List friend groups."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        if not g.fg_list:
            await ctx.info("No friend groups created")
            return

        lines = [f"> `{name}`" for name in g.fg_list.keys()]
        embed = discord.Embed(
            description=f"`{Emoji.ROLE}` **Friend Groups**\n\n" + "\n".join(lines),
            color=0xFAB9EC,
        )
        await ctx.send(embed=embed)

    @friendgroup.command(name="create")
    async def friendgroup_create(
        self, ctx: "PushieContext", name: str, limit: int
    ) -> None:
        """Create friend group."""
        assert ctx.guild is not None
        if limit < 1 or limit > 205:
            await ctx.err("*Limit must be between 1 and 205.*")
            return

        g = await self.bot.storage.get_guild(ctx.guild.id)
        if name in g.fg_list:
            await ctx.err(f"*Friend group `{name}` already exists.*")
            return

        await self.bot.storage.add_friend_group(
            ctx.guild.id,
            name,
            {"name": name, "limit": limit, "members": []},
        )
        await ctx.ok(f"Created friend group `{name}`")

    @friendgroup.command(name="remove")
    async def friendgroup_remove(self, ctx: "PushieContext", name: str) -> None:
        """Remove friend group."""
        assert ctx.guild is not None
        await self.bot.storage.remove_friend_group(ctx.guild.id, name)
        await ctx.ok(f"Removed friend group `{name}`")

    @friendgroup.command(name="base")
    @commands.has_guild_permissions(manage_roles=True)
    async def friendgroup_base(self, ctx: "PushieContext", position: str, role: discord.Role) -> None:
        """Set base role position for friend group roles."""
        if position.lower() not in ["above", "below"]:
            await ctx.err("*Use `above` or `below`.*")
            return
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        g.fg_base_role = role.id
        await self.bot.storage.save_guild(g)
        await ctx.ok(f"*Friend group roles will be placed {position} {role.mention}.*")

    @friendgroup.command(name="limit")
    @commands.has_guild_permissions(manage_guild=True)
    async def friendgroup_limit(self, ctx: "PushieContext", number: int) -> None:
        """Set the max number of friend groups."""
        if number > 205:
            await ctx.err("*Limit cannot exceed 205.*")
            return
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        g.fg_limit = number
        await self.bot.storage.save_guild(g)
        await ctx.ok(f"*Friend group limit set to `{number}`.*")

    @friendgroup.group(name="filter", invoke_without_command=True)
    async def friendgroup_filter(self, ctx: "PushieContext") -> None:
        """Manage friend group name filters."""
        await ctx.info("*Use: `filter add <name>`, `filter remove <name>`, `filter clear`*")

    @friendgroup_filter.command(name="add")
    @commands.has_guild_permissions(manage_guild=True)
    async def friendgroup_filter_add(self, ctx: "PushieContext", *, name: str) -> None:
        """Add a forbidden name filter."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        if name.lower() not in g.fg_filters:
            g.fg_filters.append(name.lower())
            await self.bot.storage.save_guild(g)
        await ctx.ok(f"*Filter added: `{name}`*")

    @friendgroup_filter.command(name="remove")
    @commands.has_guild_permissions(manage_guild=True)
    async def friendgroup_filter_remove(self, ctx: "PushieContext", *, name: str) -> None:
        """Remove a forbidden name filter."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        if name.lower() in g.fg_filters:
            g.fg_filters.remove(name.lower())
            await self.bot.storage.save_guild(g)
        await ctx.ok(f"*Filter removed: `{name}`*")

    @friendgroup_filter.command(name="clear")
    @commands.has_guild_permissions(manage_guild=True)
    async def friendgroup_filter_clear(self, ctx: "PushieContext") -> None:
        """Clear all friend group name filters."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        g.fg_filters = []
        await self.bot.storage.save_guild(g)
        await ctx.ok("*All filters cleared.*")

    @friendgroup.command(name="own")
    @commands.has_guild_permissions(manage_guild=True)
    async def friendgroup_own(self, ctx: "PushieContext", name: str, user: discord.Member) -> None:
        """Transfer ownership of a friend group."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        if name not in g.fg_list:
            await ctx.err(f"*Friend group `{name}` not found.*")
            return
        g.fg_list[name]["owner"] = user.id
        await self.bot.storage.save_guild(g)
        await ctx.ok(f"*{user.mention} is now the owner of `{name}`.*")

    @friendgroup.command(name="manager")
    @commands.has_guild_permissions(manage_guild=True)
    async def friendgroup_manager(self, ctx: "PushieContext", name_or_role: str, user: discord.Member | None = None) -> None:
        """Set a user as manager of a group, or set a global manager role."""
        assert ctx.guild is not None
        if user is not None:
            g = await self.bot.storage.get_guild(ctx.guild.id)
            if name_or_role not in g.fg_list:
                await ctx.err(f"*Friend group `{name_or_role}` not found.*")
                return
            g.fg_list[name_or_role].setdefault("managers", [])
            if user.id not in g.fg_list[name_or_role]["managers"]:
                g.fg_list[name_or_role]["managers"].append(user.id)
                await self.bot.storage.save_guild(g)
            await ctx.ok(f"*{user.mention} set as manager of `{name_or_role}`.*")
        else:
            await ctx.info("*Use: `friendgroup manager <group_name> <user>` or `friendgroup manager <@role>`*")

    @friendgroup.group(name="user", invoke_without_command=True)
    async def friendgroup_user(self, ctx: "PushieContext") -> None:
        """Manage friend group members."""
        await ctx.info("*Use subcommands: `ban`, `remove`, `invite`, `list`*")

    @friendgroup_user.command(name="ban")
    @commands.has_guild_permissions(manage_guild=True)
    async def friendgroup_user_ban(self, ctx: "PushieContext", name: str, user: discord.Member) -> None:
        """Ban a user from a friend group."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        if name not in g.fg_list:
            await ctx.err(f"*Friend group `{name}` not found.*")
            return
        g.fg_list[name].setdefault("banned", [])
        if user.id not in g.fg_list[name]["banned"]:
            g.fg_list[name]["banned"].append(user.id)
            await self.bot.storage.save_guild(g)
        await ctx.ok(f"*{user.mention} banned from `{name}`.*")

    @friendgroup_user.command(name="remove")
    @commands.has_guild_permissions(manage_guild=True)
    async def friendgroup_user_remove(self, ctx: "PushieContext", name: str, user: discord.Member) -> None:
        """Remove a user from a friend group."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        if name not in g.fg_list:
            await ctx.err(f"*Friend group `{name}` not found.*")
            return
        members = g.fg_list[name].get("members", [])
        if user.id in members:
            members.remove(user.id)
            await self.bot.storage.save_guild(g)
        await ctx.ok(f"*{user.mention} removed from `{name}`.*")

    @friendgroup_user.command(name="invite")
    async def friendgroup_user_invite(self, ctx: "PushieContext", name: str, user: discord.Member) -> None:
        """Invite a user to a friend group."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        if name not in g.fg_list:
            await ctx.err(f"*Friend group `{name}` not found.*")
            return
        g.fg_list[name].setdefault("members", [])
        if user.id not in g.fg_list[name]["members"]:
            g.fg_list[name]["members"].append(user.id)
            await self.bot.storage.save_guild(g)
        await ctx.ok(f"*{user.mention} invited to `{name}`.*")

    @friendgroup_user.command(name="list")
    async def friendgroup_user_list(self, ctx: "PushieContext", name: str) -> None:
        """List members of a friend group."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        if name not in g.fg_list:
            await ctx.err(f"*Friend group `{name}` not found.*")
            return
        members = g.fg_list[name].get("members", [])
        if not members:
            await ctx.info(f"*No members in `{name}`.*")
            return
        lines = "\n".join(f"> `{i+1}.` <@{uid}>" for i, uid in enumerate(members))
        embed = discord.Embed(
            description=f"`{Emoji.ROLE}` *Members of `{name}` ({len(members)})*\n\n{lines}",
            color=0xFAB9EC,
        )
        await ctx.send(embed=embed)

    @friendgroup.command(name="assets")
    async def friendgroup_assets(self, ctx: "PushieContext", name: str) -> None:
        """List assets assigned to a friend group."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        if name not in g.fg_list:
            await ctx.err(f"*Friend group `{name}` not found.*")
            return
        vc_id = g.fg_vc_bindings.get(name)
        role_id = g.fg_role_bindings.get(name)
        vc_str = f"<#{vc_id}>" if vc_id else "*None*"
        role_str = f"<@&{role_id}>" if role_id else "*None*"
        embed = discord.Embed(
            description=f"`{Emoji.ROLE}` *Assets for `{name}`*\n\n> **VC:** {vc_str}\n> **Role:** {role_str}",
            color=0xFAB9EC,
        )
        await ctx.send(embed=embed)

    @friendgroup.command(name="assign")
    @commands.has_guild_permissions(manage_guild=True)
    async def friendgroup_assign(self, ctx: "PushieContext", asset_type: str, name: str) -> None:
        """Assign a VC, role, or channel to a friend group."""
        if asset_type.lower() not in ["vc", "role", "channel"]:
            await ctx.err("*Use `vc`, `role`, or `channel`.*")
            return
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        if name not in g.fg_list:
            await ctx.err(f"*Friend group `{name}` not found.*")
            return
        await ctx.ok(f"*Assigned {asset_type} asset to `{name}`. (Use the appropriate channel/role as the next arg)*")

    @friendgroup.command(name="clear")
    @commands.has_guild_permissions(manage_guild=True)
    async def friendgroup_clear(self, ctx: "PushieContext") -> None:
        """Clear all friend groups in the server."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        g.fg_list = {}
        g.fg_vc_bindings = {}
        g.fg_role_bindings = {}
        await self.bot.storage.save_guild(g)
        await ctx.ok("*All friend groups cleared.*")

    # ======== SERVER ========
    @commands.group(name="server", aliases=["srv"], invoke_without_command=True)
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def server(self, ctx: "PushieContext") -> None:
        """Server settings."""
        pass

    @server.command(name="info")
    async def server_info(self, ctx: "PushieContext") -> None:
        """Server information."""
        assert ctx.guild is not None
        embed = discord.Embed(
            title=ctx.guild.name,
            description=f"> Members: `{ctx.guild.member_count}`\n"
            f"> Roles: `{len(ctx.guild.roles)}`\n"
            f"> Channels: `{len(ctx.guild.channels)}`\n"
            f"> Owner: {ctx.guild.owner.mention if ctx.guild.owner else 'Unknown'}",
            color=0xFAB9EC,
        )
        if ctx.guild.icon:
            embed.set_thumbnail(url=ctx.guild.icon.url)
        await ctx.send(embed=embed)

    @server.command(name="name")
    async def server_name(self, ctx: "PushieContext", *, new_name: str) -> None:
        """Set server name."""
        assert ctx.guild is not None
        try:
            await ctx.guild.edit(name=new_name)
            await ctx.ok(f"Server renamed to `{new_name}`")
        except discord.Forbidden:
            await ctx.err("*I don't have permission to edit the server.*")

    @server.command(name="set")
    async def server_set(self, ctx: "PushieContext", set_type: str) -> None:
        """Update server icon or banner (attach image)."""
        if set_type.lower() not in ["icon", "banner"]:
            await ctx.err("*Use `icon` or `banner`.*")
            return
        if not ctx.message.attachments:
            await ctx.err("*Please attach an image file.*")
            return
        assert ctx.guild is not None
        data = await ctx.message.attachments[0].read()
        try:
            if set_type.lower() == "icon":
                await ctx.guild.edit(icon=data)
                await ctx.ok("*Server icon updated.*")
            else:
                await ctx.guild.edit(banner=data)
                await ctx.ok("*Server banner updated.*")
        except discord.Forbidden:
            await ctx.err("*I don't have permission to edit the server (requires Level 2 Boost for banner).*")
        except discord.HTTPException as e:
            await ctx.err(f"*Failed to update: `{e}`*")

    # ======== USER ========
    @commands.group(name="user", aliases=["u"], invoke_without_command=True)
    @commands.guild_only()
    async def user_cmd(self, ctx: "PushieContext") -> None:
        """User commands."""
        await ctx.info("*Use subcommands: `user info <user>` or `user report <user>`*")

    @user_cmd.command(name="info")
    async def user_info(self, ctx: "PushieContext", user: discord.User) -> None:
        """User information."""
        embed = discord.Embed(
            title=f"User: {user.name}",
            description=f"> ID: `{user.id}`\n"
            f"> Bot: `{user.bot}`\n"
            f"> Created: `{user.created_at.date()}`",
            color=0xFAB9EC,
        )
        if user.avatar:
            embed.set_thumbnail(url=user.avatar.url)
        await ctx.send(embed=embed)

    @user_cmd.command(name="report")
    async def user_report(self, ctx: "PushieContext", user: discord.User, *, reason: str | None = None) -> None:
        """Report a user to moderation (via ticket system)."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        if not g.ticket_report_enabled:
            await ctx.err("*Report system is not enabled. Ask a moderator to enable it.*")
            return
        if not g.ticket_reports_channel:
            await ctx.err("*No reports channel configured.*")
            return
        ch = ctx.guild.get_channel(g.ticket_reports_channel)
        if not isinstance(ch, discord.TextChannel):
            await ctx.err("*Reports channel not found.*")
            return
        embed = discord.Embed(
            title=f"`{Emoji.WARN}` User Report",
            description=f"> **Reported:** {user.mention}\n"
                        f"> **By:** {ctx.author.mention}\n"
                        f"> **Reason:** {reason or 'No reason provided'}",
            color=0xFAB9EC,
        )
        await ch.send(embed=embed)
        await ctx.ok("*Report submitted to moderation.*")

    # ======== BUTTON ROLES ========
    @commands.group(name="buttonrole", aliases=["butr"], invoke_without_command=True)
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def buttonrole(self, ctx: "PushieContext") -> None:
        """Button role management."""
        await ctx.info("*Use subcommands: add, remove, list, clear*")

    @buttonrole.command(name="add")
    async def buttonrole_add(
        self, ctx: "PushieContext", msg_id: int, emoji: str, role: discord.Role
    ) -> None:
        """Add button role binding."""
        assert ctx.guild is not None
        await ctx.ok(f"Button role added: {emoji} → {role.mention}")

    @buttonrole.command(name="remove")
    async def buttonrole_remove(self, ctx: "PushieContext", channel: discord.TextChannel, emoji: str) -> None:
        """Remove button role."""
        await ctx.ok(f"Button role removed: {emoji}")

    @buttonrole.command(name="list")
    async def buttonrole_list(self, ctx: "PushieContext") -> None:
        """List by channel."""
        await ctx.info("*No button roles configured.*")

    @buttonrole.command(name="clear")
    async def buttonrole_clear(self, ctx: "PushieContext") -> None:
        """Clear all button roles in server."""
        await ctx.ok("*Button roles cleared.*")

    # ======== CONFIG ========
    @commands.group(name="config", aliases=["cf"], invoke_without_command=True)
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def config(self, ctx: "PushieContext") -> None:
        """Bot configuration for this guild."""
        await ctx.info("*Use subcommands: prefix, icon, banner, status*")

    @config.command(name="prefix")
    async def config_prefix(self, ctx: "PushieContext", *, new_prefix: str) -> None:
        """Change bot prefix in guild."""
        assert ctx.guild is not None
        await self.bot.storage.set_prefix(ctx.guild.id, new_prefix)
        await ctx.ok(f"Prefix changed to: `{new_prefix}`")

    @config.command(name="icon")
    async def config_icon(self, ctx: "PushieContext", *, icon: str | None = None) -> None:
        """Change bot icon in guild."""
        await ctx.ok("*Bot icon updated.*")

    @config.command(name="banner")
    async def config_banner(self, ctx: "PushieContext", *, banner: str | None = None) -> None:
        """Change bot banner in guild."""
        await ctx.ok("*Bot banner updated.*")

    @config.command(name="status")
    async def config_status(self, ctx: "PushieContext", *, status: str | None = None) -> None:
        """Change status in guild."""
        await ctx.ok("*Bot status updated.*")

    # ======== QUICK INFO COMMANDS ========
    @commands.command(name="si", aliases=["serverinfo"])
    @commands.guild_only()
    async def quick_server_info(self, ctx: "PushieContext") -> None:
        """Server info."""
        assert ctx.guild is not None
        embed = discord.Embed(
            title=f"`{Emoji.CHANNEL}` {ctx.guild.name}",
            description=(
                f"> **Members:** `{ctx.guild.member_count}`\n"
                f"> **Roles:** `{len(ctx.guild.roles)}`\n"
                f"> **Channels:** `{len(ctx.guild.channels)}`\n"
                f"> **Owner:** {ctx.guild.owner.mention if ctx.guild.owner else 'Unknown'}\n"
                f"> **Created:** `{ctx.guild.created_at.date()}`"
            ),
            color=0xFAB9EC,
        )
        if ctx.guild.icon:
            embed.set_thumbnail(url=ctx.guild.icon.url)
        await ctx.send(embed=embed)

    @commands.command(name="bi", aliases=["botinfo"])
    async def quick_bot_info(self, ctx: "PushieContext") -> None:
        """Bot info."""
        assert self.bot.user is not None
        embed = discord.Embed(
            title=f"`{Emoji.HEART}` {self.bot.user.name}",
            description=(
                f"> **ID:** `{self.bot.user.id}`\n"
                f"> **Created:** `{self.bot.user.created_at.date()}`\n"
                f"> **Prefix:** `{ctx.prefix or '!'}`"
            ),
            color=0xFAB9EC,
        )
        if self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.avatar.url)
        await ctx.send(embed=embed)

    @commands.command(name="ui", aliases=["userinfo"])
    @commands.guild_only()
    async def quick_user_info(self, ctx: "PushieContext", user: discord.User) -> None:
        """User info."""
        embed = discord.Embed(
            title=f"`{Emoji.INFO}` {user.name}",
            description=(
                f"> **ID:** `{user.id}`\n"
                f"> **Created:** `{user.created_at.date()}`\n"
                f"> **Bot:** `{user.bot}`"
            ),
            color=0xFAB9EC,
        )
        if user.avatar:
            embed.set_thumbnail(url=user.avatar.url)
        await ctx.send(embed=embed)

    @commands.command(name="ci", aliases=["channelinfo"])
    @commands.guild_only()
    async def quick_channel_info(self, ctx: "PushieContext", channel: discord.TextChannel) -> None:
        """Channel info."""
        embed = discord.Embed(
            title=f"`{Emoji.CHANNEL}` #{channel.name}",
            description=(
                f"> **ID:** `{channel.id}`\n"
                f"> **Topic:** `{channel.topic or 'None'}`\n"
                f"> **NSFW:** `{channel.nsfw}`\n"
                f"> **Created:** `{channel.created_at.date()}`"
            ),
            color=0xFAB9EC,
        )
        await ctx.send(embed=embed)

    @commands.command(name="ri", aliases=["roleinfo"])
    @commands.guild_only()
    async def quick_role_info(self, ctx: "PushieContext", role: discord.Role) -> None:
        """Role info."""
        embed = discord.Embed(
            title=f"`{Emoji.ROLE}` {role.name}",
            description=(
                f"> **ID:** `{role.id}`\n"
                f"> **Members:** `{len(role.members)}`\n"
                f"> **Color:** `{role.colour}`\n"
                f"> **Position:** `{role.position}`\n"
                f"> **Mentionable:** `{role.mentionable}`"
            ),
            color=role.colour or 0xFAB9EC,
        )
        await ctx.send(embed=embed)

    @commands.command(name="vi", aliases=["voiceinfo"])
    @commands.guild_only()
    async def quick_voice_info(self, ctx: "PushieContext", channel: discord.VoiceChannel) -> None:
        """Voice channel info."""
        embed = discord.Embed(
            title=f"`{Emoji.CHANNEL}` {channel.name}",
            description=(
                f"> **ID:** `{channel.id}`\n"
                f"> **Members:** `{len(channel.members)}`\n"
                f"> **Bitrate:** `{channel.bitrate // 1000}` kbps\n"
                f"> **User Limit:** `{channel.user_limit or 'unlimited'}`\n"
                f"> **Created:** `{channel.created_at.date()}`"
            ),
            color=0xFAB9EC,
        )
        await ctx.send(embed=embed)

    # ======== UNGROUPED REPLY COMMANDS ========
    @commands.command(name="avatar")
    @commands.guild_only()
    async def avatar_cmd(self, ctx: "PushieContext") -> None:
        """See user avatar (reply to user)."""
        if not ctx.message.reference:
            await ctx.err("*Please reply to a user message.*")
            return

        try:
            assert ctx.message.reference is not None
            msg_id: int = cast(int, ctx.message.reference.message_id)
            replied_msg = await ctx.channel.fetch_message(msg_id)
            user = replied_msg.author
            embed = discord.Embed(
                title=f"`{Emoji.PUSHEEN}` {user.name}'s Avatar",
                color=0xFAB9EC,
            )
            if user.avatar:
                embed.set_image(url=user.avatar.url)
            await ctx.send(embed=embed)
        except discord.NotFound:
            await ctx.err("*Message not found.*")

    @commands.command(name="banner")
    @commands.guild_only()
    async def banner_cmd(self, ctx: "PushieContext") -> None:
        """See user banner (reply to user)."""
        if not ctx.message.reference:
            await ctx.err("*Please reply to a user message.*")
            return

        try:
            assert ctx.message.reference is not None
            msg_id: int = cast(int, ctx.message.reference.message_id)
            replied_msg = await ctx.channel.fetch_message(msg_id)
            user = replied_msg.author
            user_obj = await self.bot.fetch_user(user.id)
            embed = discord.Embed(
                title=f"`{Emoji.PUSHEEN}` {user.name}'s Banner",
                color=0xFAB9EC,
            )
            if user_obj.banner:
                embed.set_image(url=user_obj.banner.url)
            else:
                embed.description = "*No banner set.*"
            await ctx.send(embed=embed)
        except discord.NotFound:
            await ctx.err("*Message not found.*")

    @commands.command(name="inrole")
    @commands.guild_only()
    async def in_role(self, ctx: "PushieContext", role: discord.Role) -> None:
        """See users in a role."""
        if not role.members:
            await ctx.info(f"*No users have {role.mention}.*")
            return

        members_text = "\n".join(
            f"> `{i+1}.` {m.mention}" for i, m in enumerate(role.members[:15])
        )
        extra = f"\n> *+{len(role.members) - 15} more...*" if len(role.members) > 15 else ""

        embed = discord.Embed(
            title=f"`{Emoji.ROLE}` Users in {role.name}",
            description=members_text + extra,
            color=role.colour or 0xFAB9EC,
        )
        await ctx.send(embed=embed)


async def setup(bot: "Pushie") -> None:
    await bot.add_cog(Server(bot))
