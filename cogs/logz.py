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

VALID_EVENT_TYPES = ["member", "mod", "role", "channel", "voice"]


class Logz(commands.Cog, name="Logz"):
    """Per-type event logging system."""

    def __init__(self, bot: "Pushie") -> None:
        self.bot = bot

    async def _send_log(self, guild: discord.Guild, event_type: str, embed: discord.Embed) -> None:
        g = self.bot.storage.get_guild_sync(guild.id)
        if not g:
            return
        ch_id: int | None = getattr(g, f"{event_type}_channel", None)
        if ch_id is None:
            ch_id = g.log_channel
        if not ch_id:
            return
        ch = guild.get_channel(ch_id)
        if isinstance(ch, discord.TextChannel):
            try:
                await ch.send(embed=embed)
            except (discord.Forbidden, discord.HTTPException):
                pass

    # ======== Listeners ========

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        embed = discord.Embed(color=0x57F287, description=f"`{Emoji.JOIN}` **Member Joined**")
        embed.set_author(name=str(member), icon_url=member.display_avatar.url)
        embed.add_field(name="User", value=member.mention, inline=True)
        embed.add_field(name="ID", value=f"`{member.id}`", inline=True)
        embed.add_field(name="Account Created", value=discord.utils.format_dt(member.created_at, "R"), inline=True)
        embed.set_footer(text=f"Member count: {member.guild.member_count}")
        await self._send_log(member.guild, "member", embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member) -> None:
        embed = discord.Embed(color=0xED4245, description=f"`{Emoji.LEAVE}` **Member Left**")
        embed.set_author(name=str(member), icon_url=member.display_avatar.url)
        embed.add_field(name="User", value=member.mention, inline=True)
        embed.add_field(name="ID", value=f"`{member.id}`", inline=True)
        roles = [r.mention for r in member.roles if r.id != member.guild.id]
        if roles:
            embed.add_field(name="Roles", value=" ".join(roles[:15]), inline=False)
        await self._send_log(member.guild, "member", embed)

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User) -> None:
        embed = discord.Embed(color=0xED4245, description=f"`{Emoji.BAN}` **Member Banned**")
        embed.set_author(name=str(user), icon_url=user.display_avatar.url)
        embed.add_field(name="User", value=user.mention, inline=True)
        embed.add_field(name="ID", value=f"`{user.id}`", inline=True)
        await self._send_log(guild, "mod", embed)

    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User) -> None:
        embed = discord.Embed(color=0x57F287, description=f"`{Emoji.UNBAN}` **Member Unbanned**")
        embed.set_author(name=str(user), icon_url=user.display_avatar.url)
        embed.add_field(name="User", value=user.mention, inline=True)
        embed.add_field(name="ID", value=f"`{user.id}`", inline=True)
        await self._send_log(guild, "mod", embed)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member) -> None:
        guild = after.guild
        if before.roles != after.roles:
            added = [r for r in after.roles if r not in before.roles]
            removed = [r for r in before.roles if r not in after.roles]
            if added or removed:
                embed = discord.Embed(color=0xFAB9EC, description=f"`{Emoji.ROLE}` **Roles Updated**")
                embed.set_author(name=str(after), icon_url=after.display_avatar.url)
                if added:
                    embed.add_field(name="Added", value=" ".join(r.mention for r in added), inline=False)
                if removed:
                    embed.add_field(name="Removed", value=" ".join(r.mention for r in removed), inline=False)
                await self._send_log(guild, "member", embed)
        if before.nick != after.nick:
            embed = discord.Embed(color=0xFAB9EC, description=f"`{Emoji.NICK}` **Nickname Changed**")
            embed.set_author(name=str(after), icon_url=after.display_avatar.url)
            embed.add_field(name="Before", value=before.nick or "*none*", inline=True)
            embed.add_field(name="After", value=after.nick or "*none*", inline=True)
            await self._send_log(guild, "member", embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message) -> None:
        if not message.guild or message.author.bot:
            return
        embed = discord.Embed(color=0xED4245, description=f"`{Emoji.DELETE}` **Message Deleted**")
        embed.set_author(name=str(message.author), icon_url=message.author.display_avatar.url)
        embed.add_field(name="Channel", value=message.channel.mention, inline=True)  # type: ignore
        if message.content:
            embed.add_field(name="Content", value=message.content[:1000], inline=False)
        embed.set_footer(text=f"User ID: {message.author.id}")
        await self._send_log(message.guild, "mod", embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message) -> None:
        if not after.guild or after.author.bot:
            return
        if before.content == after.content:
            return
        embed = discord.Embed(color=0xFEE75C, description=f"`{Emoji.EDIT}` **Message Edited**")
        embed.set_author(name=str(after.author), icon_url=after.author.display_avatar.url)
        embed.add_field(name="Channel", value=after.channel.mention, inline=True)  # type: ignore
        embed.add_field(name="Before", value=before.content[:500] or "*empty*", inline=False)
        embed.add_field(name="After", value=after.content[:500] or "*empty*", inline=False)
        embed.set_footer(text=f"User ID: {after.author.id}")
        await self._send_log(after.guild, "mod", embed)

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel) -> None:
        embed = discord.Embed(color=0x57F287, description=f"`{Emoji.CHANNEL}` **Channel Created**")
        embed.add_field(name="Name", value=getattr(channel, "mention", f"`#{channel.name}`"), inline=True)
        embed.add_field(name="Type", value=str(channel.type), inline=True)
        embed.add_field(name="ID", value=f"`{channel.id}`", inline=True)
        await self._send_log(channel.guild, "channel", embed)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel) -> None:
        embed = discord.Embed(color=0xED4245, description=f"`{Emoji.DELETE}` **Channel Deleted**")
        embed.add_field(name="Name", value=f"`#{channel.name}`", inline=True)
        embed.add_field(name="Type", value=str(channel.type), inline=True)
        embed.add_field(name="ID", value=f"`{channel.id}`", inline=True)
        await self._send_log(channel.guild, "channel", embed)

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before: discord.abc.GuildChannel, after: discord.abc.GuildChannel) -> None:
        if before.name == after.name:
            return
        embed = discord.Embed(color=0xFEE75C, description=f"`{Emoji.EDIT}` **Channel Updated**")
        embed.add_field(name="Before", value=f"`#{before.name}`", inline=True)
        embed.add_field(name="After", value=getattr(after, "mention", f"`#{after.name}`"), inline=True)
        await self._send_log(after.guild, "channel", embed)

    @commands.Cog.listener()
    async def on_guild_role_create(self, role: discord.Role) -> None:
        embed = discord.Embed(color=0x57F287, description=f"`{Emoji.ROLE}` **Role Created**")
        embed.add_field(name="Name", value=role.mention, inline=True)
        embed.add_field(name="ID", value=f"`{role.id}`", inline=True)
        embed.add_field(name="Color", value=f"`{role.color}`", inline=True)
        await self._send_log(role.guild, "role", embed)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role) -> None:
        embed = discord.Embed(color=0xED4245, description=f"`{Emoji.DELETE}` **Role Deleted**")
        embed.add_field(name="Name", value=f"`@{role.name}`", inline=True)
        embed.add_field(name="ID", value=f"`{role.id}`", inline=True)
        await self._send_log(role.guild, "role", embed)

    @commands.Cog.listener()
    async def on_guild_role_update(self, before: discord.Role, after: discord.Role) -> None:
        if before.name == after.name and before.color == after.color:
            return
        embed = discord.Embed(color=0xFEE75C, description=f"`{Emoji.EDIT}` **Role Updated**")
        embed.add_field(name="Role", value=after.mention, inline=True)
        if before.name != after.name:
            embed.add_field(name="Name", value=f"`{before.name}` → `{after.name}`", inline=True)
        if before.color != after.color:
            embed.add_field(name="Color", value=f"`{before.color}` → `{after.color}`", inline=True)
        await self._send_log(after.guild, "role", embed)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState) -> None:
        guild = member.guild
        if before.channel == after.channel:
            return
        if before.channel and not after.channel:
            embed = discord.Embed(color=0xED4245, description=f"`{Emoji.LEAVE}` **Left Voice**")
        elif not before.channel and after.channel:
            embed = discord.Embed(color=0x57F287, description=f"`{Emoji.JOIN}` **Joined Voice**")
        else:
            embed = discord.Embed(color=0xFEE75C, description=f"`{Emoji.EDIT}` **Moved Voice**")
        embed.set_author(name=str(member), icon_url=member.display_avatar.url)
        if before.channel:
            embed.add_field(name="From", value=f"`{before.channel.name}`", inline=True)
        if after.channel:
            embed.add_field(name="To", value=f"`{after.channel.name}`", inline=True)
        await self._send_log(guild, "voice", embed)

    # ======== Commands ========

    @commands.group(name="logz", aliases=["lg"], invoke_without_command=True)
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def logz(self, ctx: "PushieContext") -> None:
        """Event logging configuration."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        lines = []
        general = f"<#{g.log_channel}>" if g.log_channel else "*not set*"
        lines.append(f"> **general** — {general}")
        for et in VALID_EVENT_TYPES:
            ch_id = getattr(g, f"{et}_channel", None)
            ch_txt = f"<#{ch_id}>" if ch_id else "*inherits general*"
            lines.append(f"> **{et}** — {ch_txt}")
        prefix = ctx.prefix or "!"
        await ctx.send(
            embed=UI.info(
                f"`{Emoji.CHANNEL}` **Log Channels**\n\n"
                + "\n".join(lines)
                + f"\n\n```\n{prefix}logz add <type> <channel>\n"
                f"{prefix}logz remove <type>\n"
                f"{prefix}logz view\n"
                f"{prefix}logz color <hex>\n"
                f"{prefix}logz test <type>\n```"
            )
        )

    @logz.command(name="add")
    async def logz_add(self, ctx: "PushieContext", event_type: str, channel: discord.TextChannel) -> None:
        """Set a log channel for an event type (member/mod/role/channel/voice/general)."""
        assert ctx.guild is not None
        et = event_type.lower()
        if et not in VALID_EVENT_TYPES and et != "general":
            await ctx.err(f"*Valid types: `{', '.join(VALID_EVENT_TYPES)}, general`*")
            return
        if et == "general":
            await self.bot.storage.update_setup(ctx.guild.id, log_channel=channel.id)
        else:
            await self.bot.storage.update_setup(ctx.guild.id, **{f"{et}_channel": channel.id})
        await ctx.ok(f"`{et}` logs → {channel.mention}")

    @logz.command(name="remove")
    async def logz_remove(self, ctx: "PushieContext", event_type: str) -> None:
        """Remove a log channel assignment."""
        assert ctx.guild is not None
        et = event_type.lower()
        if et not in VALID_EVENT_TYPES and et != "general":
            await ctx.err(f"*Valid types: `{', '.join(VALID_EVENT_TYPES)}, general`*")
            return
        if et == "general":
            await self.bot.storage.update_setup(ctx.guild.id, log_channel=None)
        else:
            await self.bot.storage.update_setup(ctx.guild.id, **{f"{et}_channel": None})
        await ctx.ok(f"`{et}` log channel removed")

    @logz.command(name="view")
    async def logz_view(self, ctx: "PushieContext") -> None:
        """View all log channel assignments."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        lines = [f"> **general** — {'<#' + str(g.log_channel) + '>' if g.log_channel else '*not set*'}"]
        for et in VALID_EVENT_TYPES:
            ch_id = getattr(g, f"{et}_channel", None)
            ch_txt = f"<#{ch_id}>" if ch_id else "*inherits general*"
            lines.append(f"> **{et}** — {ch_txt}")
        await ctx.send(embed=UI.info(f"`{Emoji.CHANNEL}` **Log Channels**\n\n" + "\n".join(lines)))

    @logz.command(name="color")
    async def logz_color(self, ctx: "PushieContext", hex_color: str) -> None:
        """Set log embed color."""
        assert ctx.guild is not None
        try:
            color = int(hex_color.lstrip("#"), 16)
        except ValueError:
            await ctx.err("*Invalid hex color. Example: `#FAB9EC`*")
            return
        await self.bot.storage.update_setup(ctx.guild.id, log_color=color)
        embed = discord.Embed(color=color, description=f"`{Emoji.SUCCESS}` *Log color updated.*")
        await ctx.send(embed=embed)

    @logz.command(name="test")
    async def logz_test(self, ctx: "PushieContext", event_type: str = "member") -> None:
        """Send a test log to the channel for that event type."""
        assert ctx.guild is not None
        et = event_type.lower()
        if et not in VALID_EVENT_TYPES and et != "general":
            await ctx.err(f"*Valid types: `{', '.join(VALID_EVENT_TYPES)}, general`*")
            return
        embed = discord.Embed(color=0xFAB9EC, description=f"`{Emoji.INFO}` **Test Log — `{et}`**\nThis is a test log message.")
        embed.set_footer(text="Log test by " + str(ctx.author))
        g = await self.bot.storage.get_guild(ctx.guild.id)
        if et == "general":
            ch_id = g.log_channel
        else:
            ch_id = getattr(g, f"{et}_channel", None) or g.log_channel
        if not ch_id:
            await ctx.err(f"*No log channel set for `{et}`. Use `logz add {et} <channel>` first.*")
            return
        ch = ctx.guild.get_channel(ch_id)
        if isinstance(ch, discord.TextChannel):
            await ch.send(embed=embed)
            await ctx.ok(f"*Test log sent to {ch.mention}.*")
        else:
            await ctx.err("*Log channel not found or not a text channel.*")


async def setup(bot: "Pushie") -> None:
    await bot.add_cog(Logz(bot))
