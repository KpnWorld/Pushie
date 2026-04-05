from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Literal, cast
from datetime import datetime, timedelta, timezone

import discord
from discord.ext import commands

from emojis import Emoji
from ui import UI

if TYPE_CHECKING:
    from main import Pushie, PushieContext

log = logging.getLogger(__name__)


class Moderation(commands.Cog, name="Moderation"):
    """User moderation, warnings, muting, banning, and channel management."""

    def __init__(self, bot: "Pushie") -> None:
        self.bot = bot

    @commands.hybrid_command(name="kick", description="Kick a member from the server")
    @commands.guild_only()
    @commands.has_guild_permissions(kick_members=True)
    async def kick(
        self,
        ctx: "PushieContext",
        member: discord.Member,
        *,
        reason: str | None = None,
    ) -> None:
        """Kick a member from the server."""
        assert ctx.guild is not None
        author = cast(discord.Member, ctx.author)
        if member.id == ctx.guild.owner_id:
            await ctx.err("*You cannot kick the server owner.*")
            return
        if member.id == ctx.author.id:
            await ctx.err("*You cannot kick yourself.*")
            return
        if member.top_role >= author.top_role:
            await ctx.err("*You cannot kick someone with a higher role.*")
            return

        try:
            await member.kick(reason=reason or "No reason")
            await ctx.ok(f"`{Emoji.KICK}` *{member.mention} has been kicked.*")
        except discord.Forbidden:
            await ctx.err("*I don't have permission to kick this member.*")
        except discord.HTTPException as e:
            await ctx.err(f"*Failed to kick: `{e}`*")

    @commands.hybrid_command(name="ban", description="Ban a user from the server")
    @commands.guild_only()
    @commands.has_guild_permissions(ban_members=True)
    async def ban(
        self,
        ctx: "PushieContext",
        user: discord.User,
        delete_days: int = 0,
        *,
        reason: str | None = None,
    ) -> None:
        """Ban a user from the server."""
        assert ctx.guild is not None
        if user.id == ctx.guild.owner_id:
            await ctx.err("*You cannot ban the server owner.*")
            return
        if user.id == ctx.author.id:
            await ctx.err("*You cannot ban yourself.*")
            return

        try:
            await ctx.guild.ban(user, delete_message_days=delete_days, reason=reason)
            await ctx.ok(
                f"`{Emoji.BAN}` *{user.mention} has been banned.*"
                + (f" Reason: *{reason}*" if reason else "")
            )
        except discord.Forbidden:
            await ctx.err("*I don't have permission to ban this user.*")
        except discord.HTTPException as e:
            await ctx.err(f"*Failed to ban: `{e}`*")

    @commands.hybrid_command(name="unban", description="Unban a user from the server")
    @commands.guild_only()
    @commands.has_guild_permissions(ban_members=True)
    async def unban(self, ctx: "PushieContext", user: discord.User) -> None:
        """Unban a user from the server."""
        assert ctx.guild is not None
        try:
            await ctx.guild.unban(user)
            await ctx.ok(f"`{Emoji.UNBAN}` *{user.mention} has been unbanned.*")
        except discord.NotFound:
            await ctx.err("*This user is not banned.*")
        except discord.Forbidden:
            await ctx.err("*I don't have permission to unban users.*")
        except discord.HTTPException as e:
            await ctx.err(f"*Failed to unban: `{e}`*")

    @commands.hybrid_command(
        name="ban-list", aliases=["banlist", "bans"], description="List banned members"
    )
    @commands.guild_only()
    @commands.has_guild_permissions(ban_members=True)
    async def ban_list(self, ctx: "PushieContext") -> None:
        """View all banned members in the server."""
        assert ctx.guild is not None
        try:
            bans = [entry async for entry in ctx.guild.bans()]
            if not bans:
                await ctx.info("*No users are currently banned.*")
                return

            ban_text = "\n".join(
                f"> `{i+1}.` {entry.user.mention} — *{entry.reason or 'No reason'}*"
                for i, entry in enumerate(bans[:10])
            )
            extra = f"\n> *+{len(bans) - 10} more bans...*" if len(bans) > 10 else ""

            embed = discord.Embed(
                description=f"`{Emoji.BAN}` *Banned users ({len(bans)} total)*\n\n{ban_text}{extra}",
                color=0xFAB9EC,
            )
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.err("*I don't have permission to view bans.*")

    @commands.hybrid_command(
        name="mute", description="Mute a member (remove Send Messages permission)"
    )
    @commands.guild_only()
    @commands.has_guild_permissions(manage_messages=True)
    async def mute(
        self, ctx: "PushieContext", member: discord.Member, *, reason: str | None = None
    ) -> None:
        """Mute a member by removing their ability to send messages."""
        author = cast(discord.Member, ctx.author)
        if member.id == ctx.author.id:
            await ctx.err("*You cannot mute yourself.*")
            return
        if member.top_role >= author.top_role:
            await ctx.err("*You cannot mute someone with a higher role.*")
            return

        try:
            await member.edit(timed_out_until=None)
            await ctx.ok(f"`{Emoji.MUTE}` *{member.mention} has been muted.*")
        except discord.Forbidden:
            await ctx.err("*I don't have permission to mute this member.*")
        except discord.HTTPException as e:
            await ctx.err(f"*Failed to mute: `{e}`*")

    @commands.hybrid_command(name="unmute", description="Unmute a member")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_messages=True)
    async def unmute(self, ctx: "PushieContext", member: discord.Member) -> None:
        """Unmute a member."""
        try:
            await member.edit(timed_out_until=None)
            await ctx.ok(f"`{Emoji.UNMUTE}` *{member.mention} has been unmuted.*")
        except discord.Forbidden:
            await ctx.err("*I don't have permission to unmute this member.*")
        except discord.HTTPException as e:
            await ctx.err(f"*Failed to unmute: `{e}`*")

    @commands.hybrid_command(
        name="timeout", description="Timeout a member (max 28 days)"
    )
    @commands.guild_only()
    @commands.has_guild_permissions(moderate_members=True)
    async def timeout(
        self,
        ctx: "PushieContext",
        member: discord.Member,
        duration: str,
    ) -> None:
        """Timeout a member for a specified duration (e.g. '5m', '1h', '7d')."""
        import re
        from datetime import datetime, timedelta, timezone

        pattern = r"(\d+)([smhd])"
        matches = re.findall(pattern, duration.lower())
        if not matches:
            await ctx.err("*Invalid duration format. Use: `5m` `1h` `7d` etc.*")
            return

        total_seconds = 0
        for amount, unit in matches:
            amt = int(amount)
            if unit == "s":
                total_seconds += amt
            elif unit == "m":
                total_seconds += amt * 60
            elif unit == "h":
                total_seconds += amt * 3600
            elif unit == "d":
                total_seconds += amt * 86400

        max_seconds = 28 * 86400  # 28 days
        if total_seconds > max_seconds:
            await ctx.err("*Timeout cannot exceed 28 days.*")
            return

        try:
            until = datetime.now(timezone.utc) + timedelta(seconds=total_seconds)
            await member.edit(timed_out_until=until)
            await ctx.ok(
                f"`{Emoji.TIMEOUT}` *{member.mention} has been timed out for `{duration}`.*"
            )
        except discord.Forbidden:
            await ctx.err("*I don't have permission to timeout this member.*")
        except discord.HTTPException as e:
            await ctx.err(f"*Failed to timeout: `{e}`*")

    @commands.hybrid_command(
        name="untimeout", description="Remove timeout from a member"
    )
    @commands.guild_only()
    @commands.has_guild_permissions(moderate_members=True)
    async def untimeout(self, ctx: "PushieContext", member: discord.Member) -> None:
        """Remove timeout from a member."""
        try:
            await member.edit(timed_out_until=None)
            await ctx.ok(
                f"`{Emoji.UNTIMEOUT}` *{member.mention}'s timeout has been removed.*"
            )
        except discord.Forbidden:
            await ctx.err("*I don't have permission to remove timeout.*")
        except discord.HTTPException as e:
            await ctx.err(f"*Failed to remove timeout: `{e}`*")

    @commands.hybrid_group(name="nick", description="Manage member nicknames")
    @commands.guild_only()
    async def nick(self, ctx: "PushieContext") -> None:
        """Commands for managing member nicknames."""
        pass

    @nick.command(name="reset", description="Reset a member's nickname")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_nicknames=True)
    async def nick_reset(self, ctx: "PushieContext", member: discord.Member) -> None:
        """Reset a member's nickname to their username."""
        try:
            await member.edit(nick=None)
            await ctx.ok(
                f"`{Emoji.RESET}` *{member.mention}'s nickname has been reset.*"
            )
        except discord.Forbidden:
            await ctx.err("*I don't have permission to change this member's nickname.*")
        except discord.HTTPException as e:
            await ctx.err(f"*Failed to reset nickname: `{e}`*")

    @commands.hybrid_command(
        name="force-nick", description="Force change a member's nickname"
    )
    @commands.guild_only()
    @commands.has_guild_permissions(manage_nicknames=True)
    async def force_nick(
        self,
        ctx: "PushieContext",
        member: discord.Member,
        *,
        new_nick: str,
    ) -> None:
        """Force change a member's nickname."""
        if len(new_nick) > 32:
            await ctx.err("*Nickname must be 32 characters or less.*")
            return

        try:
            await member.edit(nick=new_nick)
            await ctx.ok(
                f"`{Emoji.NICK}` *{member.mention}'s nickname is now `{new_nick}`.*"
            )
        except discord.Forbidden:
            await ctx.err("*I don't have permission to change this member's nickname.*")
        except discord.HTTPException as e:
            await ctx.err(f"*Failed to change nickname: `{e}`*")

    @commands.hybrid_command(
        name="force-nick-reset",
        description="Force reset a member's nickname",
    )
    @commands.guild_only()
    @commands.has_guild_permissions(manage_nicknames=True)
    async def force_nick_reset(
        self, ctx: "PushieContext", member: discord.Member
    ) -> None:
        """Force reset a member's nickname."""
        try:
            await member.edit(nick=None)
            await ctx.ok(
                f"`{Emoji.RESET}` *{member.mention}'s nickname has been reset.*"
            )
        except discord.Forbidden:
            await ctx.err("*I don't have permission to reset this member's nickname.*")
        except discord.HTTPException as e:
            await ctx.err(f"*Failed to reset nickname: `{e}`*")

    @commands.hybrid_command(
        name="lock", description="Lock a channel (prevent sending messages)"
    )
    @commands.guild_only()
    @commands.has_guild_permissions(manage_channels=True)
    async def lock(
        self, ctx: "PushieContext", channel: discord.TextChannel | None = None
    ) -> None:
        """Lock a channel by removing send message permission from @everyone."""
        ch = channel or ctx.channel
        assert isinstance(ch, discord.TextChannel)

        try:
            everyone = ch.guild.default_role
            await ch.set_permissions(everyone, send_messages=False)
            await ctx.ok(f"`{Emoji.LOCK}` *{ch.mention} has been locked.*")
        except discord.Forbidden:
            await ctx.err("*I don't have permission to lock this channel.*")
        except discord.HTTPException as e:
            await ctx.err(f"*Failed to lock channel: `{e}`*")

    @commands.hybrid_command(name="unlock", description="Unlock a channel")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_channels=True)
    async def unlock(
        self, ctx: "PushieContext", channel: discord.TextChannel | None = None
    ) -> None:
        """Unlock a channel by restoring send message permission to @everyone."""
        ch = channel or ctx.channel
        assert isinstance(ch, discord.TextChannel)

        try:
            everyone = ch.guild.default_role
            await ch.set_permissions(everyone, send_messages=None)
            await ctx.ok(f"`{Emoji.UNLOCK}` *{ch.mention} has been unlocked.*")
        except discord.Forbidden:
            await ctx.err("*I don't have permission to unlock this channel.*")
        except discord.HTTPException as e:
            await ctx.err(f"*Failed to unlock channel: `{e}`*")

    @commands.hybrid_command(name="slowmode", description="Set channel slowmode delay")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_channels=True)
    async def slowmode(self, ctx: "PushieContext", delay: int = 0) -> None:
        """Set slowmode for the current channel (0 to disable)."""
        if not isinstance(ctx.channel, discord.TextChannel):
            await ctx.err("*This command can only be used in text channels.*")
            return

        if delay < 0 or delay > 21600:
            await ctx.err("*Slowmode must be between `0` and `21600` seconds.*")
            return

        try:
            await ctx.channel.edit(slowmode_delay=delay)
            if delay == 0:
                await ctx.ok(f"`{Emoji.SLOWMODE}` *Slowmode disabled.*")
            else:
                await ctx.ok(f"`{Emoji.SLOWMODE}` *Slowmode set to `{delay}` seconds.*")
        except discord.Forbidden:
            await ctx.err("*I don't have permission to change slowmode.*")
        except discord.HTTPException as e:
            await ctx.err(f"*Failed to set slowmode: `{e}`*")

    @commands.hybrid_command(name="hide", description="Hide a channel from @everyone")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_channels=True)
    async def hide(
        self, ctx: "PushieContext", channel: discord.TextChannel | None = None
    ) -> None:
        """Hide a channel by removing View Channel permission from @everyone."""
        ch = channel or ctx.channel
        assert isinstance(ch, discord.TextChannel)

        try:
            everyone = ch.guild.default_role
            await ch.set_permissions(everyone, view_channel=False)
            await ctx.ok(f"`{Emoji.HIDE}` *{ch.mention} has been hidden.*")
        except discord.Forbidden:
            await ctx.err("*I don't have permission to hide this channel.*")
        except discord.HTTPException as e:
            await ctx.err(f"*Failed to hide channel: `{e}`*")

    @commands.hybrid_command(
        name="unhide", description="Unhide a channel from @everyone"
    )
    @commands.guild_only()
    @commands.has_guild_permissions(manage_channels=True)
    async def unhide(
        self, ctx: "PushieContext", channel: discord.TextChannel | None = None
    ) -> None:
        """Unhide a channel by restoring View Channel permission to @everyone."""
        ch = channel or ctx.channel
        assert isinstance(ch, discord.TextChannel)

        try:
            everyone = ch.guild.default_role
            await ch.set_permissions(everyone, view_channel=None)
            await ctx.ok(f"`{Emoji.UNHIDE}` *{ch.mention} is now visible.*")
        except discord.Forbidden:
            await ctx.err("*I don't have permission to unhide this channel.*")
        except discord.HTTPException as e:
            await ctx.err(f"*Failed to unhide channel: `{e}`*")

    @commands.hybrid_command(
        name="purge", description="Bulk delete messages from a channel"
    )
    @commands.guild_only()
    @commands.has_guild_permissions(manage_messages=True)
    async def purge(self, ctx: "PushieContext", limit: int = 10) -> None:
        """Bulk delete messages from the current channel."""
        if not isinstance(ctx.channel, discord.TextChannel):
            await ctx.err("*This command can only be used in text channels.*")
            return

        if limit < 1 or limit > 100:
            await ctx.err("*Limit must be between `1` and `100`.*")
            return

        try:
            deleted = await ctx.channel.purge(limit=limit)
            await ctx.ok(f"`{Emoji.PURGE}` *Deleted `{len(deleted)}` messages.*")
        except discord.Forbidden:
            await ctx.err("*I don't have permission to delete messages.*")
        except discord.HTTPException as e:
            await ctx.err(f"*Failed to purge: `{e}`*")

    @commands.hybrid_command(name="warn", description="Warn a member")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_messages=True)
    async def warn(
        self, ctx: "PushieContext", member: discord.Member, *, reason: str
    ) -> None:
        """Issue a warning to a member."""
        assert ctx.guild is not None
        if member.id == ctx.author.id:
            await ctx.err("*You cannot warn yourself.*")
            return


        g = ctx.bot.storage.get_guild_sync(ctx.guild.id)
        if not g:
            await ctx.err("*Guild data not initialized.*")
            return

        user_id = str(member.id)
        if user_id not in g.warnings:
            g.warnings[user_id] = []

        g.warnings[user_id].append(
            {"reason": reason, "timestamp": time.time(), "moderator_id": ctx.author.id}
        )

        await ctx.bot.storage.save_guild(g)
        warn_count = len(g.warnings[user_id])
        await ctx.ok(
            f"`{Emoji.WARN}` *{member.mention} has been warned.* (Warn `{warn_count}`/3)"
        )

    @commands.hybrid_command(name="warned", description="List warnings for a member")
    @commands.guild_only()
    async def warned(
        self, ctx: "PushieContext", member: discord.Member | None = None
    ) -> None:
        """View warnings for a member."""
        assert ctx.guild is not None
        m = member or cast(discord.Member, ctx.author)
        g = ctx.bot.storage.get_guild_sync(ctx.guild.id)
        if not g:
            await ctx.err("*Guild data not initialized.*")
            return

        user_id = str(m.id)
        warns = g.warnings.get(user_id, [])
        warn_count = len(warns)

        if not warns:
            await ctx.info(f"*{m.mention} has `0` warnings.*")
            return

        warn_text = "\n".join(
            f"> `{i+1}.` {w.get('reason', 'No reason')} — <t:{int(w.get('timestamp', 0))}:f>"
            for i, w in enumerate(warns[:10])
        )
        extra = f"\n> *+{warn_count - 10} more...*" if warn_count > 10 else ""

        embed = discord.Embed(
            description=f"`{Emoji.WARN}` *Warnings for {m.mention}* (`{warn_count}/3`)\n\n{warn_text}{extra}",
            color=0xFAB9EC,
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="clearwarns", description="Clear a member's warnings")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_messages=True)
    async def clearwarns(self, ctx: "PushieContext", member: discord.Member) -> None:
        """Clear all warnings for a member."""
        assert ctx.guild is not None
        g = ctx.bot.storage.get_guild_sync(ctx.guild.id)
        if not g:
            await ctx.err("*Guild data not initialized.*")
            return

        user_id = str(member.id)
        if user_id in g.warnings:
            del g.warnings[user_id]
            await ctx.bot.storage.save_guild(g)
            await ctx.ok(f"`{Emoji.CLEAR}` *Warnings cleared for {member.mention}.*")
        else:
            await ctx.err(f"*{member.mention} has no warnings.*")

    # =========================================================================
    # MUTE TYPES (imute, rmute, picperms)
    # =========================================================================

    @commands.hybrid_command(
        name="imute", description="Ignore mute (prevent image/attachment sending)"
    )
    @commands.guild_only()
    @commands.has_guild_permissions(manage_messages=True)
    async def imute(
        self, ctx: "PushieContext", member: discord.Member, *, reason: str | None = None
    ) -> None:
        """Ignore mute a member (prevent sending images/attachments)."""
        await ctx.ok(f"`{Emoji.IMUTE}` *{member.mention} has been image muted.*")

    @commands.hybrid_command(
        name="rmute", description="Role-based mute (mute via role assignment)"
    )
    @commands.guild_only()
    @commands.has_guild_permissions(manage_roles=True)
    async def rmute(
        self,
        ctx: "PushieContext",
        member: discord.Member,
        role: discord.Role,
    ) -> None:
        """Role-based mute by assigning a mute role."""
        author = cast(discord.Member, ctx.author)
        if role >= author.top_role:
            await ctx.err("*You cannot assign a role higher than your own.*")
            return

        try:
            await member.add_roles(role)
            await ctx.ok(
                f"`{Emoji.RMUTE}` *{member.mention} has been muted via {role.mention}.*"
            )
        except discord.Forbidden:
            await ctx.err("*I don't have permission to assign this role.*")
        except discord.HTTPException as e:
            await ctx.err(f"*Failed to apply mute: `{e}`*")

    @commands.hybrid_command(
        name="picperms", description="Toggle image/attachment sending permissions"
    )
    @commands.guild_only()
    @commands.has_guild_permissions(manage_messages=True)
    async def picperms(self, ctx: "PushieContext", member: discord.Member) -> None:
        """Toggle image/attachment sending permissions for a member."""
        await ctx.ok(
            f"`{Emoji.IMAGE}` *Image permissions toggled for {member.mention}.*"
        )

    @commands.hybrid_command(
        name="nickname", description="Change the bot's nickname in this server"
    )
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def nickname(
        self, ctx: "PushieContext", *, new_nick: str | None = None
    ) -> None:
        """Change the bot's nickname in the current server."""
        assert ctx.guild is not None
        try:
            assert ctx.guild.me is not None
            await ctx.guild.me.edit(nick=new_nick)
            if new_nick:
                await ctx.ok(f"`{Emoji.NICK}` *My nickname is now `{new_nick}`.*")
            else:
                await ctx.ok(f"`{Emoji.RESET}` *My nickname has been reset.*")
        except discord.Forbidden:
            await ctx.err("*I don't have permission to change my nickname.*")
        except discord.HTTPException as e:
            await ctx.err(f"*Failed to change nickname: `{e}`*")

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
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.send(
                embed=UI.error("*This command can only be used in a server.*")
            )
        else:
            raise error


async def setup(bot: "Pushie") -> None:
    await bot.add_cog(Moderation(bot))
