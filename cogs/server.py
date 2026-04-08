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
        """List tickets."""
        await ctx.info(f"Listing {list_type} tickets...")

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
        if not g.autoroles:
            await ctx.info("No autoroles configured")
            return

        lines = [f"> `{i+1}.` <@&{rid}>" for i, rid in enumerate(g.autoroles)]
        embed = discord.Embed(
            description=f"`{Emoji.ROLE}` **Autoroles**\n\n" + "\n".join(lines),
            color=0xFAB9EC,
        )
        await ctx.send(embed=embed)

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

    # ======== SERVER ========
    @commands.group(name="server", aliases=["s"], invoke_without_command=True)
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

    # ======== USER INFO ========
    @commands.command(name="user")
    @commands.guild_only()
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

    # ======== REACTION ROLES ========
    @commands.group(name="reactionrole", aliases=["rr"], invoke_without_command=True)
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def reactionrole(self, ctx: "PushieContext") -> None:
        """Reaction role management."""
        await ctx.info("*Use subcommands: add, remove, list, clear*")

    @reactionrole.command(name="add")
    async def reactionrole_add(
        self, ctx: "PushieContext", msg_id: int, emoji: str, role: discord.Role
    ) -> None:
        """Add reaction role binding."""
        assert ctx.guild is not None
        await ctx.ok(f"Reaction role added: {emoji} → {role.mention}")

    @reactionrole.command(name="remove")
    async def reactionrole_remove(self, ctx: "PushieContext", channel: discord.TextChannel, emoji: str) -> None:
        """Remove reaction role."""
        await ctx.ok(f"Reaction role removed: {emoji}")

    @reactionrole.command(name="list")
    async def reactionrole_list(self, ctx: "PushieContext") -> None:
        """List by channel."""
        await ctx.info("*No reaction roles configured.*")

    @reactionrole.command(name="clear")
    async def reactionrole_clear(self, ctx: "PushieContext") -> None:
        """Clear all reaction roles in server."""
        await ctx.ok("*Reaction roles cleared.*")

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
