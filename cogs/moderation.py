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
        # In-memory snipe caches keyed by channel_id
        self._snipes: dict[int, dict] = {}
        self._editsnipes: dict[int, dict] = {}
        self._reactionsnipes: dict[int, dict] = {}
        # Tracks running mass-role operations so they can be cancelled
        self._mass_role_tasks: dict[int, bool] = {}

    # ======== Snipe Listeners ========
    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message) -> None:
        if message.author.bot or not message.guild:
            return
        self._snipes[message.channel.id] = {
            "author": message.author,
            "content": message.content,
            "attachments": [a.url for a in message.attachments],
            "timestamp": message.created_at,
        }

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message) -> None:
        if before.author.bot or not before.guild:
            return
        if before.content == after.content:
            return
        self._editsnipes[before.channel.id] = {
            "author": before.author,
            "before": before.content,
            "after": after.content,
            "timestamp": before.created_at,
        }

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent) -> None:
        if payload.guild_id is None:
            return
        self._reactionsnipes[payload.channel_id] = {
            "user_id": payload.user_id,
            "emoji": str(payload.emoji),
            "message_id": payload.message_id,
        }

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member) -> None:
        """Re-apply forced nicks if changed."""
        if before.nick == after.nick:
            return
        g = self.bot.storage.get_guild_sync(after.guild.id)
        if not g:
            return
        forced = g.forced_nicks.get(str(after.id))
        if forced and after.nick != forced:
            try:
                await after.edit(nick=forced, reason="Forced nick re-applied")
            except (discord.Forbidden, discord.HTTPException):
                pass

    @commands.command(name="kick")
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

    @commands.command(name="ban")
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

    @commands.command(name="unban")
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

    @commands.command(name="ban-list", aliases=["banlist", "bans"])
    @commands.guild_only()
    @commands.has_guild_permissions(ban_members=True)
    async def ban_list(self, ctx: "PushieContext") -> None:
        """View all banned members in the server."""
        assert ctx.guild is not None

        if ctx.interaction:
            await ctx.interaction.response.defer()

        async def _reply(embed: discord.Embed) -> None:
            if ctx.interaction:
                try:
                    await ctx.interaction.followup.send(embed=embed)
                except (discord.NotFound, discord.HTTPException):
                    pass
            else:
                await ctx.send(embed=embed)

        try:
            bans = [entry async for entry in ctx.guild.bans()]
            if not bans:
                await _reply(UI.info("*No users are currently banned.*"))
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
            await _reply(embed)
        except discord.Forbidden:
            await _reply(UI.error("*I don't have permission to view bans.*"))

    @commands.command(name="mute")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_messages=True)
    async def mute(
        self, ctx: "PushieContext", member: discord.Member, *, reason: str | None = None
    ) -> None:
        """Mute a member by assigning the configured mute role."""
        assert ctx.guild is not None
        author = cast(discord.Member, ctx.author)
        if member.id == ctx.author.id:
            await ctx.err("*You cannot mute yourself.*")
            return
        if member.top_role >= author.top_role:
            await ctx.err("*You cannot mute someone with a higher role.*")
            return

        g = ctx.bot.storage.get_guild_sync(ctx.guild.id)
        if not g or not g.mute_role:
            await ctx.err("*No mute role configured. Use `/setup` to set one up.*")
            return
        mute_role = ctx.guild.get_role(g.mute_role)
        if not mute_role:
            await ctx.err("*Mute role not found. Please reconfigure it in `/setup`.*")
            return
        if mute_role in member.roles:
            await ctx.err(f"*{member.mention} is already muted.*")
            return

        try:
            await member.add_roles(mute_role, reason=reason or "Muted via /mute")
            await ctx.ok(f"`{Emoji.MUTE}` *{member.mention} has been muted.*")
        except discord.Forbidden:
            await ctx.err("*I don't have permission to assign the mute role.*")
        except discord.HTTPException as e:
            await ctx.err(f"*Failed to mute: `{e}`*")

    @commands.command(name="unmute")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_messages=True)
    async def unmute(self, ctx: "PushieContext", member: discord.Member) -> None:
        """Unmute a member by removing the configured mute role."""
        assert ctx.guild is not None

        g = ctx.bot.storage.get_guild_sync(ctx.guild.id)
        if not g or not g.mute_role:
            await ctx.err("*No mute role configured. Use `/setup` to set one up.*")
            return
        mute_role = ctx.guild.get_role(g.mute_role)
        if not mute_role:
            await ctx.err("*Mute role not found. Please reconfigure it in `/setup`.*")
            return
        if mute_role not in member.roles:
            await ctx.err(f"*{member.mention} is not muted.*")
            return

        try:
            await member.remove_roles(mute_role, reason="Unmuted via /unmute")
            await ctx.ok(f"`{Emoji.UNMUTE}` *{member.mention} has been unmuted.*")
        except discord.Forbidden:
            await ctx.err("*I don't have permission to remove the mute role.*")
        except discord.HTTPException as e:
            await ctx.err(f"*Failed to unmute: `{e}`*")

    @commands.group(name="timeout", invoke_without_command=True)
    @commands.guild_only()
    @commands.has_guild_permissions(moderate_members=True)
    async def timeout(
        self,
        ctx: "PushieContext",
        member: discord.Member | None = None,
        duration: str | None = None,
    ) -> None:
        """Timeout a member for a specified duration (e.g. '5m', '1h', '7d')."""
        if member is None or duration is None:
            await ctx.info("*Use: `timeout <user> <duration>` | `timeout list` | `timeout remove <user>`*")
            return
        import re as _re
        pattern = r"(\d+)([smhd])"
        matches = _re.findall(pattern, duration.lower())
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

        max_seconds = 28 * 86400
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

    @timeout.command(name="list")
    @commands.guild_only()
    @commands.has_guild_permissions(moderate_members=True)
    async def timeout_list_cmd(self, ctx: "PushieContext") -> None:
        """List timed-out members."""
        assert ctx.guild is not None
        timed_out = [m for m in ctx.guild.members if m.is_timed_out()]
        if not timed_out:
            await ctx.info("*No members are currently timed out.*")
            return
        lines = "\n".join(f"> `{i+1}.` {m.mention}" for i, m in enumerate(timed_out[:15]))
        embed = discord.Embed(
            description=f"`{Emoji.TIMEOUT}` *Timed-out members ({len(timed_out)})*\n\n{lines}",
            color=0xFAB9EC,
        )
        await ctx.send(embed=embed)

    @timeout.command(name="remove")
    @commands.guild_only()
    @commands.has_guild_permissions(moderate_members=True)
    async def timeout_remove_cmd(self, ctx: "PushieContext", member: discord.Member) -> None:
        """Remove a member's timeout."""
        try:
            await member.edit(timed_out_until=None)
            await ctx.ok(f"`{Emoji.UNTIMEOUT}` *{member.mention}'s timeout removed.*")
        except discord.Forbidden:
            await ctx.err("*I don't have permission to remove this member's timeout.*")
        except discord.HTTPException as e:
            await ctx.err(f"*Failed to remove timeout: `{e}`*")

    @commands.command(name="untimeout")
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

    @commands.group(name="nick", aliases=["nickname"], invoke_without_command=True)
    @commands.guild_only()
    @commands.has_guild_permissions(manage_nicknames=True)
    async def nick(self, ctx: "PushieContext", member: discord.Member | None = None, *, nickname: str | None = None) -> None:
        """Set a member's nickname."""
        if member is None:
            await ctx.info("*Use: `nick <user> <nickname>` or `nick remove <user>`*")
            return
        if nickname is None:
            await ctx.err("*Please provide a nickname.*")
            return
        if len(nickname) > 32:
            await ctx.err("*Nickname must be 32 characters or less.*")
            return
        try:
            await member.edit(nick=nickname)
            await ctx.ok(f"`{Emoji.NICK}` *{member.mention}'s nickname set to `{nickname}`.*")
        except discord.Forbidden:
            await ctx.err("*I don't have permission to change this member's nickname.*")
        except discord.HTTPException as e:
            await ctx.err(f"*Failed to set nickname: `{e}`*")

    @nick.command(name="remove")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_nicknames=True)
    async def nick_remove(self, ctx: "PushieContext", member: discord.Member) -> None:
        """Remove a member's nickname."""
        try:
            await member.edit(nick=None)
            await ctx.ok(f"`{Emoji.RESET}` *{member.mention}'s nickname has been removed.*")
        except discord.Forbidden:
            await ctx.err("*I don't have permission to change this member's nickname.*")
        except discord.HTTPException as e:
            await ctx.err(f"*Failed to remove nickname: `{e}`*")

    @commands.group(name="forcenick", aliases=["fn"], invoke_without_command=True)
    @commands.guild_only()
    @commands.has_guild_permissions(manage_nicknames=True)
    async def forcenick(self, ctx: "PushieContext", member: discord.Member | None = None, *, nickname: str | None = None) -> None:
        """Force a nickname on a member (persists across rejoins)."""
        if member is None or nickname is None:
            await ctx.info("*Use: `forcenick <user> <nickname>` or `forcenick cancel <user>`*")
            return
        if len(nickname) > 32:
            await ctx.err("*Nickname must be 32 characters or less.*")
            return
        assert ctx.guild is not None
        try:
            await member.edit(nick=nickname)
            g = await ctx.bot.storage.get_guild(ctx.guild.id)
            g.forced_nicks[str(member.id)] = nickname
            await ctx.bot.storage.save_guild(g)
            await ctx.ok(f"`{Emoji.NICK}` *{member.mention}'s nickname has been forced to `{nickname}`.*")
        except discord.Forbidden:
            await ctx.err("*I don't have permission to change this member's nickname.*")
        except discord.HTTPException as e:
            await ctx.err(f"*Failed to force nickname: `{e}`*")

    @forcenick.command(name="cancel")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_nicknames=True)
    async def forcenick_cancel(self, ctx: "PushieContext", member: discord.Member) -> None:
        """Remove a forced nickname."""
        assert ctx.guild is not None
        try:
            await member.edit(nick=None)
            g = await ctx.bot.storage.get_guild(ctx.guild.id)
            g.forced_nicks.pop(str(member.id), None)
            await ctx.bot.storage.save_guild(g)
            await ctx.ok(f"`{Emoji.RESET}` *Forced nickname removed for {member.mention}.*")
        except discord.Forbidden:
            await ctx.err("*I don't have permission to reset this member's nickname.*")
        except discord.HTTPException as e:
            await ctx.err(f"*Failed to cancel forced nickname: `{e}`*")

    @commands.command(name="lock")
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

    @commands.command(name="unlock")
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

    @commands.command(name="slowmode", aliases=["slowmod"])
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

    @commands.command(name="hide")
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

    @commands.command(name="unhide")
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

    @commands.group(name="purge", aliases=["pur"], invoke_without_command=True)
    @commands.guild_only()
    @commands.has_guild_permissions(manage_messages=True)
    async def purge(self, ctx: "PushieContext", limit: int = 10) -> None:
        """Bulk delete messages from a channel."""
        if ctx.interaction:
            await ctx.interaction.response.defer(ephemeral=True)

        if not isinstance(ctx.channel, discord.TextChannel):
            await ctx.err("*This command can only be used in text channels.*")
            return

        if limit < 1 or limit > 100:
            await ctx.err("*Limit must be between `1` and `100`.*")
            return

        async def _reply(embed: discord.Embed) -> None:
            if ctx.interaction:
                try:
                    await ctx.interaction.followup.send(embed=embed, ephemeral=True)
                except (discord.NotFound, discord.HTTPException):
                    pass
            else:
                await ctx.send(embed=embed)

        try:
            deleted = await ctx.channel.purge(limit=limit)
            await _reply(UI.success(f"`{Emoji.PURGE}` *Deleted `{len(deleted)}` messages.*"))
        except discord.Forbidden:
            await _reply(UI.error("*I don't have permission to delete messages.*"))
        except discord.HTTPException as e:
            await _reply(UI.error(f"*Failed to purge: `{e}`*"))

    @purge.command(name="user")
    async def purge_user(self, ctx: "PushieContext", user: discord.User, amount: int = 50) -> None:
        """Purge messages from a specific user."""
        if not isinstance(ctx.channel, discord.TextChannel):
            await ctx.err("*This command can only be used in text channels.*")
            return
        try:
            deleted = await ctx.channel.purge(limit=min(amount, 200), check=lambda m: m.author.id == user.id)
            await ctx.ok(f"`{Emoji.PURGE}` *Deleted `{len(deleted)}` messages from {user.mention}.*")
        except discord.Forbidden:
            await ctx.err("*I don't have permission to delete messages.*")

    @purge.command(name="embeds")
    async def purge_embeds(self, ctx: "PushieContext", limit: int = 50) -> None:
        """Purge messages with embeds."""
        if not isinstance(ctx.channel, discord.TextChannel):
            await ctx.err("*This command can only be used in text channels.*")
            return
        try:
            deleted = await ctx.channel.purge(limit=min(limit, 200), check=lambda m: bool(m.embeds))
            await ctx.ok(f"`{Emoji.PURGE}` *Deleted `{len(deleted)}` embed messages.*")
        except discord.Forbidden:
            await ctx.err("*I don't have permission to delete messages.*")

    @purge.command(name="images")
    async def purge_images(self, ctx: "PushieContext", limit: int = 50) -> None:
        """Purge messages with images/attachments."""
        if not isinstance(ctx.channel, discord.TextChannel):
            await ctx.err("*This command can only be used in text channels.*")
            return
        try:
            deleted = await ctx.channel.purge(limit=min(limit, 200), check=lambda m: bool(m.attachments))
            await ctx.ok(f"`{Emoji.PURGE}` *Deleted `{len(deleted)}` image messages.*")
        except discord.Forbidden:
            await ctx.err("*I don't have permission to delete messages.*")

    @purge.command(name="voice")
    async def purge_voice(self, ctx: "PushieContext", limit: int = 50) -> None:
        """Purge voice messages."""
        if not isinstance(ctx.channel, discord.TextChannel):
            await ctx.err("*This command can only be used in text channels.*")
            return
        try:
            deleted = await ctx.channel.purge(
                limit=min(limit, 200),
                check=lambda m: any(a.content_type and "audio" in a.content_type for a in m.attachments)
            )
            await ctx.ok(f"`{Emoji.PURGE}` *Deleted `{len(deleted)}` voice messages.*")
        except discord.Forbidden:
            await ctx.err("*I don't have permission to delete messages.*")

    @purge.command(name="mentions")
    async def purge_mentions(self, ctx: "PushieContext", limit: int = 50) -> None:
        """Purge messages with user mentions."""
        if not isinstance(ctx.channel, discord.TextChannel):
            await ctx.err("*This command can only be used in text channels.*")
            return
        try:
            deleted = await ctx.channel.purge(limit=min(limit, 200), check=lambda m: bool(m.mentions))
            await ctx.ok(f"`{Emoji.PURGE}` *Deleted `{len(deleted)}` mention messages.*")
        except discord.Forbidden:
            await ctx.err("*I don't have permission to delete messages.*")

    @purge.command(name="humans")
    async def purge_humans(self, ctx: "PushieContext", limit: int = 50) -> None:
        """Purge messages from humans only."""
        if not isinstance(ctx.channel, discord.TextChannel):
            await ctx.err("*This command can only be used in text channels.*")
            return
        try:
            deleted = await ctx.channel.purge(limit=min(limit, 200), check=lambda m: not m.author.bot)
            await ctx.ok(f"`{Emoji.PURGE}` *Deleted `{len(deleted)}` messages from humans.*")
        except discord.Forbidden:
            await ctx.err("*I don't have permission to delete messages.*")

    @purge.command(name="bots")
    async def purge_bots(self, ctx: "PushieContext", limit: int = 50) -> None:
        """Purge messages from bots only."""
        if not isinstance(ctx.channel, discord.TextChannel):
            await ctx.err("*This command can only be used in text channels.*")
            return
        try:
            deleted = await ctx.channel.purge(limit=min(limit, 200), check=lambda m: m.author.bot)
            await ctx.ok(f"`{Emoji.PURGE}` *Deleted `{len(deleted)}` bot messages.*")
        except discord.Forbidden:
            await ctx.err("*I don't have permission to delete messages.*")

    @purge.command(name="invites")
    async def purge_invites(self, ctx: "PushieContext", limit: int = 50) -> None:
        """Purge messages containing Discord invite links."""
        import re as _re
        invite_pattern = _re.compile(r"discord\.gg/|discord\.com/invite/")
        if not isinstance(ctx.channel, discord.TextChannel):
            await ctx.err("*This command can only be used in text channels.*")
            return
        try:
            deleted = await ctx.channel.purge(
                limit=min(limit, 200),
                check=lambda m: bool(invite_pattern.search(m.content))
            )
            await ctx.ok(f"`{Emoji.PURGE}` *Deleted `{len(deleted)}` invite messages.*")
        except discord.Forbidden:
            await ctx.err("*I don't have permission to delete messages.*")

    @purge.command(name="before")
    async def purge_before(self, ctx: "PushieContext", msg_id: int, limit: int = 100) -> None:
        """Purge messages before a specific message ID."""
        if not isinstance(ctx.channel, discord.TextChannel):
            await ctx.err("*This command can only be used in text channels.*")
            return
        try:
            target = discord.Object(id=msg_id)
            deleted = await ctx.channel.purge(limit=min(limit, 200), before=target)
            await ctx.ok(f"`{Emoji.PURGE}` *Deleted `{len(deleted)}` messages before that message.*")
        except discord.Forbidden:
            await ctx.err("*I don't have permission to delete messages.*")

    @purge.command(name="after")
    async def purge_after(self, ctx: "PushieContext", msg_id: int, limit: int = 100) -> None:
        """Purge messages after a specific message ID."""
        if not isinstance(ctx.channel, discord.TextChannel):
            await ctx.err("*This command can only be used in text channels.*")
            return
        try:
            target = discord.Object(id=msg_id)
            deleted = await ctx.channel.purge(limit=min(limit, 200), after=target)
            await ctx.ok(f"`{Emoji.PURGE}` *Deleted `{len(deleted)}` messages after that message.*")
        except discord.Forbidden:
            await ctx.err("*I don't have permission to delete messages.*")

    @purge.command(name="with")
    async def purge_with(self, ctx: "PushieContext", *, keyword: str) -> None:
        """Purge messages containing a keyword."""
        if not isinstance(ctx.channel, discord.TextChannel):
            await ctx.err("*This command can only be used in text channels.*")
            return
        try:
            deleted = await ctx.channel.purge(
                limit=200,
                check=lambda m: keyword.lower() in m.content.lower()
            )
            await ctx.ok(f"`{Emoji.PURGE}` *Deleted `{len(deleted)}` messages containing `{keyword}`.*")
        except discord.Forbidden:
            await ctx.err("*I don't have permission to delete messages.*")

    @commands.group(name="warn", aliases=["w"], invoke_without_command=True)
    @commands.guild_only()
    @commands.has_guild_permissions(manage_messages=True)
    async def warn(
        self, ctx: "PushieContext", member: discord.Member | None = None, *, reason: str = "No reason"
    ) -> None:
        """Issue a warning to a member."""
        if member is None:
            await ctx.info("*Use: `warn <user> [reason]` or `warn list/clear/strikes`*")
            return
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
            f"`{Emoji.WARN}` *{member.mention} has been warned.* (Warn `{warn_count}`)"
        )

    @warn.command(name="list")
    @commands.guild_only()
    async def warn_list(self, ctx: "PushieContext", member: discord.Member) -> None:
        """List user warns."""
        assert ctx.guild is not None
        g = ctx.bot.storage.get_guild_sync(ctx.guild.id)
        if not g:
            await ctx.err("*Guild data not initialized.*")
            return

        user_id = str(member.id)
        warns = g.warnings.get(user_id, [])
        warn_count = len(warns)

        if not warns:
            await ctx.info(f"*{member.mention} has `0` warnings.*")
            return

        warn_text = "\n".join(
            f"> `{i+1}.` {w.get('reason', 'No reason')} — <t:{int(w.get('timestamp', 0))}:f>"
            for i, w in enumerate(warns[:10])
        )
        extra = f"\n> *+{warn_count - 10} more...*" if warn_count > 10 else ""

        embed = discord.Embed(
            description=f"`{Emoji.WARN}` *Warnings for {member.mention}* (`{warn_count}`)\n\n{warn_text}{extra}",
            color=0xFAB9EC,
        )
        await ctx.send(embed=embed)

    @warn.command(name="clear")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_messages=True)
    async def warn_clear(
        self, ctx: "PushieContext", member: discord.Member, amount: str = "all"
    ) -> None:
        """Clear warns for a user (amount or 'all')."""
        assert ctx.guild is not None
        g = ctx.bot.storage.get_guild_sync(ctx.guild.id)
        if not g:
            await ctx.err("*Guild data not initialized.*")
            return

        user_id = str(member.id)
        if user_id not in g.warnings or not g.warnings[user_id]:
            await ctx.err(f"*{member.mention} has no warnings.*")
            return

        if amount == "all":
            del g.warnings[user_id]
            await ctx.bot.storage.save_guild(g)
            await ctx.ok(f"`{Emoji.CLEAR}` *All warnings cleared for {member.mention}.*")
        else:
            try:
                n = int(amount)
                g.warnings[user_id] = g.warnings[user_id][n:]
                if not g.warnings[user_id]:
                    del g.warnings[user_id]
                await ctx.bot.storage.save_guild(g)
                await ctx.ok(f"`{Emoji.CLEAR}` *Cleared `{n}` warning(s) for {member.mention}.*")
            except ValueError:
                await ctx.err("*Amount must be a number or `all`.*")

    @warn.command(name="strikes")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def warn_strikes(self, ctx: "PushieContext", count: int, *, action: str) -> None:
        """Set the action triggered at a given warn strike count."""
        await ctx.ok(f"`{Emoji.WARN}` *At `{count}` warns: `{action}` will be applied.*")

    # =========================================================================
    # MUTE TYPES (imute, rmute, picperms)
    # =========================================================================

    @commands.command(name="imute")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_messages=True)
    async def imute(
        self, ctx: "PushieContext", member: discord.Member, *, reason: str | None = None
    ) -> None:
        """Image mute a member by assigning the configured imute role."""
        assert ctx.guild is not None
        author = cast(discord.Member, ctx.author)
        if member.id == ctx.author.id:
            await ctx.err("*You cannot image mute yourself.*")
            return
        if member.top_role >= author.top_role:
            await ctx.err("*You cannot image mute someone with a higher role.*")
            return

        g = ctx.bot.storage.get_guild_sync(ctx.guild.id)
        if not g or not g.imute_role:
            await ctx.err("*No image mute role configured. Use `/setup` to set one up.*")
            return
        imute_role = ctx.guild.get_role(g.imute_role)
        if not imute_role:
            await ctx.err("*Image mute role not found. Please reconfigure it in `/setup`.*")
            return
        if imute_role in member.roles:
            await ctx.err(f"*{member.mention} is already image muted.*")
            return

        try:
            await member.add_roles(imute_role, reason=reason or "Image muted via /imute")
            await ctx.ok(f"`{Emoji.IMUTE}` *{member.mention} has been image muted.*")
        except discord.Forbidden:
            await ctx.err("*I don't have permission to assign the image mute role.*")
        except discord.HTTPException as e:
            await ctx.err(f"*Failed to image mute: `{e}`*")

    @commands.command(name="rmute")
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

    @commands.command(name="picperms")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_messages=True)
    async def picperms(self, ctx: "PushieContext", member: discord.Member) -> None:
        """Toggle image/attachment sending permissions for a member."""
        await ctx.ok(
            f"`{Emoji.IMAGE}` *Image permissions toggled for {member.mention}.*"
        )


    # ======== MOD SETUP ========
    @commands.group(name="mod-setup", invoke_without_command=True)
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def mod_setup(self, ctx: "PushieContext") -> None:
        """Setup moderation environment (creates jail + mute roles)."""
        assert ctx.guild is not None
        msg = await ctx.send(embed=UI.loading("*Setting up moderation roles...*"))
        created = []
        try:
            # Jail role
            jail_role = discord.utils.get(ctx.guild.roles, name="Jailed")
            if not jail_role:
                jail_role = await ctx.guild.create_role(name="Jailed", reason="mod-setup")
                created.append("Jailed role")
            # Muted role
            mute_role = discord.utils.get(ctx.guild.roles, name="Muted")
            if not mute_role:
                mute_role = await ctx.guild.create_role(name="Muted", reason="mod-setup")
                created.append("Muted role")
            # Image Muted role
            imute_role = discord.utils.get(ctx.guild.roles, name="Image Muted")
            if not imute_role:
                imute_role = await ctx.guild.create_role(name="Image Muted", reason="mod-setup")
                created.append("Image Muted role")
            # Reaction Muted role
            rmute_role = discord.utils.get(ctx.guild.roles, name="Reaction Muted")
            if not rmute_role:
                rmute_role = await ctx.guild.create_role(name="Reaction Muted", reason="mod-setup")
                created.append("Reaction Muted role")
            # Jail channel
            jail_cat = discord.utils.get(ctx.guild.categories, name="Jail")
            if not jail_cat:
                overwrites = {
                    ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False),
                    jail_role: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
                    ctx.guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True),
                }
                jail_cat = await ctx.guild.create_category("Jail", overwrites=overwrites, reason="mod-setup")
                created.append("Jail category")
            jail_channel = discord.utils.get(ctx.guild.text_channels, name="jail")
            if not jail_channel:
                jail_channel = await jail_cat.create_text_channel("jail", reason="mod-setup")
                created.append("jail channel")
            # Apply mute overrides to all text channels
            for ch in ctx.guild.text_channels:
                try:
                    await ch.set_permissions(mute_role, send_messages=False, reason="mod-setup")
                    await ch.set_permissions(imute_role, attach_files=False, embed_links=False, reason="mod-setup")
                    await ch.set_permissions(rmute_role, add_reactions=False, reason="mod-setup")
                except (discord.Forbidden, discord.HTTPException):
                    pass
            await ctx.bot.storage.update_setup(
                ctx.guild.id,
                jail_role=jail_role.id,
                jail_channel=jail_channel.id,
                mute_role=mute_role.id,
                imute_role=imute_role.id,
                rmute_role=rmute_role.id,
            )
            summary = "\n".join(f"> `✓` {c}" for c in created) if created else "> *All roles already exist*"
            await msg.edit(embed=UI.success(f"`{Emoji.SETUP}` *Moderation setup complete!*\n\n{summary}"))
        except discord.Forbidden:
            await msg.edit(embed=UI.error("*I don't have enough permissions to set up moderation.*"))
        except discord.HTTPException as e:
            await msg.edit(embed=UI.error(f"*Setup failed: `{e}`*"))

    @mod_setup.command(name="reset")
    async def mod_setup_reset(self, ctx: "PushieContext") -> None:
        """Reset moderation setup."""
        assert ctx.guild is not None
        await ctx.bot.storage.update_setup(
            ctx.guild.id,
            jail_role=None, jail_channel=None,
            mute_role=None, imute_role=None, rmute_role=None,
        )
        await ctx.ok("*Moderation setup reset.*")

    @mod_setup.command(name="sync")
    async def mod_setup_sync(self, ctx: "PushieContext") -> None:
        """Re-apply permission overrides for mute/jail roles."""
        assert ctx.guild is not None
        g = ctx.bot.storage.get_guild_sync(ctx.guild.id)
        if not g:
            await ctx.err("*Guild data not available.*")
            return
        synced = 0
        for role_attr, perm_kwargs in [
            ("mute_role", {"send_messages": False}),
            ("imute_role", {"attach_files": False, "embed_links": False}),
            ("rmute_role", {"add_reactions": False}),
        ]:
            rid = getattr(g, role_attr)
            if not rid:
                continue
            role = ctx.guild.get_role(rid)
            if not role:
                continue
            for ch in ctx.guild.text_channels:
                try:
                    await ch.set_permissions(role, **perm_kwargs, reason="mod-setup sync")
                    synced += 1
                except (discord.Forbidden, discord.HTTPException):
                    pass
        await ctx.ok(f"`{Emoji.SYNC}` *Synced `{synced}` channel permission(s).*")

    # ======== SNIPE ========
    @commands.command(name="snipe", aliases=["s"])
    @commands.guild_only()
    async def snipe(self, ctx: "PushieContext") -> None:
        """Snipe last deleted message in this channel."""
        data = self._snipes.get(ctx.channel.id)  # type: ignore
        if not data:
            await ctx.info("*No recently deleted messages in this channel.*")
            return
        author: discord.User | discord.Member = data["author"]
        embed = discord.Embed(
            description=data["content"] or "*[no text]*",
            color=0xFAB9EC,
            timestamp=data["timestamp"],
        )
        embed.set_author(name=str(author), icon_url=author.display_avatar.url)
        embed.set_footer(text="Deleted")
        if data.get("attachments"):
            embed.set_image(url=data["attachments"][0])
        await ctx.send(embed=embed)

    @commands.command(name="reactionsnipe", aliases=["rs"])
    @commands.guild_only()
    async def reactionsnipe(self, ctx: "PushieContext") -> None:
        """Snipe last removed reaction in this channel."""
        data = self._reactionsnipes.get(ctx.channel.id)  # type: ignore
        if not data:
            await ctx.info("*No recent reaction removals in this channel.*")
            return
        embed = discord.Embed(
            description=f"<@{data['user_id']}> removed {data['emoji']} from [message](https://discord.com/channels/{ctx.guild.id}/{ctx.channel.id}/{data['message_id']})",  # type: ignore
            color=0xFAB9EC,
        )
        embed.set_footer(text="Reaction Snipe")
        await ctx.send(embed=embed)

    @commands.command(name="editsnipe", aliases=["es"])
    @commands.guild_only()
    async def editsnipe(self, ctx: "PushieContext") -> None:
        """Snipe last edited message in this channel."""
        data = self._editsnipes.get(ctx.channel.id)  # type: ignore
        if not data:
            await ctx.info("*No recently edited messages in this channel.*")
            return
        author: discord.User | discord.Member = data["author"]
        embed = discord.Embed(color=0xFAB9EC, timestamp=data["timestamp"])
        embed.set_author(name=str(author), icon_url=author.display_avatar.url)
        embed.add_field(name="Before", value=data["before"][:1000] or "*empty*", inline=False)
        embed.add_field(name="After", value=data["after"][:1000] or "*empty*", inline=False)
        embed.set_footer(text="Edit Snipe")
        await ctx.send(embed=embed)

    @commands.command(name="clearsnipes", aliases=["cs"])
    @commands.guild_only()
    @commands.has_guild_permissions(manage_messages=True)
    async def clearsnipes(self, ctx: "PushieContext") -> None:
        """Clear snipes in current channel."""
        ch_id = ctx.channel.id  # type: ignore
        self._snipes.pop(ch_id, None)
        self._editsnipes.pop(ch_id, None)
        self._reactionsnipes.pop(ch_id, None)
        await ctx.ok("*Snipes cleared for this channel.*")

    # ======== INVOKE ========
    @commands.group(name="invoke", aliases=["iv"], invoke_without_command=True)
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def invoke(self, ctx: "PushieContext") -> None:
        """Invoke message configuration."""
        prefix = ctx.prefix or "!"
        await ctx.send(
            embed=UI.info(
                f"`{Emoji.INFO}` **Invoke Messages**\n\n"
                f"```\n{prefix}invoke jail {{channel/dm}} <message>\n"
                f"{prefix}invoke ban {{channel/dm}} <message>\n"
                f"{prefix}invoke timeout {{channel/dm}} <message>\n"
                f"{prefix}invoke mute {{channel/dm}} <message>\n"
                f"{prefix}invoke warn {{channel/dm}} <message>\n"
                f"{prefix}invoke list\n"
                f"{prefix}invoke reset\n"
                f"{prefix}invoke remove {{type}}\n```"
            )
        )

    async def _set_invoke(self, ctx: "PushieContext", action: str, delivery: str, message: str) -> None:
        assert ctx.guild is not None
        g = await ctx.bot.storage.get_guild(ctx.guild.id)
        if action not in g.invoke_messages:
            g.invoke_messages[action] = {}
        g.invoke_messages[action][delivery] = message
        await ctx.bot.storage.save_guild(g)
        await ctx.ok(f"*Invoke message for `{action}` ({delivery}) set.*")

    @invoke.command(name="jail")
    async def invoke_jail(self, ctx: "PushieContext", delivery: str = "channel", *, message: str = "") -> None:
        """Set invoke message for jail. Delivery: channel or dm."""
        if not message:
            await ctx.err("*Please provide a message.*")
            return
        await self._set_invoke(ctx, "jail", delivery, message)

    @invoke.command(name="ban")
    async def invoke_ban(self, ctx: "PushieContext", delivery: str = "channel", *, message: str = "") -> None:
        """Set invoke message for ban."""
        if not message:
            await ctx.err("*Please provide a message.*")
            return
        await self._set_invoke(ctx, "ban", delivery, message)

    @invoke.command(name="timeout")
    async def invoke_timeout(self, ctx: "PushieContext", delivery: str = "channel", *, message: str = "") -> None:
        """Set invoke message for timeout."""
        if not message:
            await ctx.err("*Please provide a message.*")
            return
        await self._set_invoke(ctx, "timeout", delivery, message)

    @invoke.command(name="mute")
    async def invoke_mute(self, ctx: "PushieContext", delivery: str = "channel", *, message: str = "") -> None:
        """Set invoke message for mute."""
        if not message:
            await ctx.err("*Please provide a message.*")
            return
        await self._set_invoke(ctx, "mute", delivery, message)

    @invoke.command(name="warn")
    async def invoke_warn(self, ctx: "PushieContext", delivery: str = "channel", *, message: str = "") -> None:
        """Set invoke message for warn."""
        if not message:
            await ctx.err("*Please provide a message.*")
            return
        await self._set_invoke(ctx, "warn", delivery, message)

    @invoke.command(name="list")
    async def invoke_list(self, ctx: "PushieContext") -> None:
        """List current invoke messages."""
        assert ctx.guild is not None
        g = await ctx.bot.storage.get_guild(ctx.guild.id)
        if not g.invoke_messages:
            await ctx.info("*No invoke messages configured.*")
            return
        lines = []
        for action, deliveries in g.invoke_messages.items():
            for delivery, msg in deliveries.items():
                lines.append(f"> **{action}** ({delivery}): `{msg[:60]}`")
        await ctx.send(embed=UI.info(f"`{Emoji.INFO}` **Invoke Messages**\n\n" + "\n".join(lines)))

    @invoke.command(name="reset")
    async def invoke_reset(self, ctx: "PushieContext") -> None:
        """Reset all invoke messages."""
        assert ctx.guild is not None
        await ctx.bot.storage.update_setup(ctx.guild.id, invoke_messages={})
        await ctx.ok("*All invoke messages reset.*")

    @invoke.command(name="remove")
    async def invoke_remove(self, ctx: "PushieContext", message_type: str) -> None:
        """Remove invoke message for a specific type."""
        assert ctx.guild is not None
        g = await ctx.bot.storage.get_guild(ctx.guild.id)
        if message_type in g.invoke_messages:
            del g.invoke_messages[message_type]
            await ctx.bot.storage.save_guild(g)
            await ctx.ok(f"*Invoke message for `{message_type}` removed.*")
        else:
            await ctx.err(f"*No invoke message for `{message_type}`.*")

    # ======== JAIL ========
    @commands.command(name="jail")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_messages=True)
    async def jail(self, ctx: "PushieContext", member: discord.Member, *, reason: str | None = None) -> None:
        """Jail a member."""
        assert ctx.guild is not None
        g = ctx.bot.storage.get_guild_sync(ctx.guild.id)
        if not g or not g.jail_role:
            await ctx.err("*No jail role configured. Use `mod-setup` first.*")
            return
        jail_role = ctx.guild.get_role(g.jail_role)
        if not jail_role:
            await ctx.err("*Jail role not found. Please reconfigure via `mod-setup`.*")
            return
        try:
            await member.add_roles(jail_role, reason=reason or "Jailed")
            if member.id not in g.jailed:
                g.jailed.append(member.id)
                await ctx.bot.storage.save_guild(g)
            await ctx.ok(f"`{Emoji.JAIL}` *{member.mention} has been jailed.*")
        except discord.Forbidden:
            await ctx.err("*I don't have permission to jail this member.*")

    @commands.command(name="unjail")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_messages=True)
    async def unjail(self, ctx: "PushieContext", member: discord.Member) -> None:
        """Unjail a member."""
        assert ctx.guild is not None
        g = ctx.bot.storage.get_guild_sync(ctx.guild.id)
        if not g or not g.jail_role:
            await ctx.err("*No jail role configured.*")
            return
        jail_role = ctx.guild.get_role(g.jail_role)
        if not jail_role:
            await ctx.err("*Jail role not found.*")
            return
        try:
            await member.remove_roles(jail_role, reason="Unjailed")
            if member.id in g.jailed:
                g.jailed.remove(member.id)
                await ctx.bot.storage.save_guild(g)
            await ctx.ok(f"`{Emoji.UNJAIL}` *{member.mention} has been unjailed.*")
        except discord.Forbidden:
            await ctx.err("*I don't have permission to unjail this member.*")

    @commands.command(name="jailed")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_messages=True)
    async def jailed(self, ctx: "PushieContext") -> None:
        """List all jailed members."""
        assert ctx.guild is not None
        g = ctx.bot.storage.get_guild_sync(ctx.guild.id)
        if not g or not g.jailed:
            await ctx.info("*No members are currently jailed.*")
            return
        lines = "\n".join(f"> `{i+1}.` <@{uid}>" for i, uid in enumerate(g.jailed))
        embed = discord.Embed(
            description=f"`{Emoji.JAIL}` *Jailed members ({len(g.jailed)})*\n\n{lines}",
            color=0xFAB9EC,
        )
        await ctx.send(embed=embed)

    # ======== STRIP ========
    @commands.command(name="strip")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_roles=True)
    async def strip(self, ctx: "PushieContext", member: discord.Member) -> None:
        """Strip moderation permissions from a member."""
        assert ctx.guild is not None
        author = cast(discord.Member, ctx.author)
        mod_perms = discord.Permissions(
            kick_members=True, ban_members=True, manage_messages=True,
            manage_roles=True, mute_members=True, deafen_members=True,
            move_members=True, moderate_members=True,
        )
        roles_to_remove = [
            r for r in member.roles
            if r.permissions.value & mod_perms.value and r < author.top_role
        ]
        if not roles_to_remove:
            await ctx.info(f"*{member.mention} has no moderation roles to strip.*")
            return
        try:
            await member.remove_roles(*roles_to_remove, reason="Strip mod perms")
            await ctx.ok(f"`{Emoji.CLEAR}` *Stripped `{len(roles_to_remove)}` moderation role(s) from {member.mention}.*")
        except discord.Forbidden:
            await ctx.err("*I don't have permission to remove those roles.*")

    # ======== NSFW ========
    @commands.command(name="nsfw")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_channels=True)
    async def nsfw(self, ctx: "PushieContext", channel: discord.TextChannel | None = None) -> None:
        """Toggle NSFW on a channel."""
        ch = channel or ctx.channel
        assert isinstance(ch, discord.TextChannel)
        try:
            await ch.edit(nsfw=not ch.nsfw)
            state = "enabled" if not ch.nsfw else "disabled"
            await ctx.ok(f"`{Emoji.CHANNEL}` *NSFW {state} for {ch.mention}.*")
        except discord.Forbidden:
            await ctx.err("*I don't have permission to edit this channel.*")

    # ======== LOCKDOWN ========
    @commands.group(name="lockdown", aliases=["ld"], invoke_without_command=True)
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def lockdown(self, ctx: "PushieContext") -> None:
        """Lockdown the entire server."""
        assert ctx.guild is not None
        everyone = ctx.guild.default_role
        locked = 0
        for ch in ctx.guild.text_channels:
            try:
                await ch.set_permissions(everyone, send_messages=False)
                locked += 1
            except (discord.Forbidden, discord.HTTPException):
                pass
        await ctx.ok(f"`{Emoji.LOCK}` *Server locked down. (`{locked}` channels locked)*")

    @lockdown.command(name="staff")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def lockdown_staff(self, ctx: "PushieContext", role: discord.Role) -> None:
        """Set a staff role exempt from lockdown."""
        assert ctx.guild is not None
        await ctx.bot.storage.update_setup(ctx.guild.id, lockdown_staff_role=role.id)
        await ctx.ok(f"`{Emoji.WHITELIST}` *{role.mention} set as lockdown-exempt staff role.*")

    @commands.command(name="unlockdown", aliases=["uld"])
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def unlockdown(self, ctx: "PushieContext") -> None:
        """Unlock the entire server."""
        assert ctx.guild is not None
        everyone = ctx.guild.default_role
        unlocked = 0
        for ch in ctx.guild.text_channels:
            try:
                await ch.set_permissions(everyone, send_messages=None)
                unlocked += 1
            except (discord.Forbidden, discord.HTTPException):
                pass
        await ctx.ok(f"`{Emoji.UNLOCK}` *Server unlocked. (`{unlocked}` channels restored)*")

    # (timeout list / timeout remove are subcommands of the timeout group above)

    # ======== IUNMUTE / RUNMUTE ========
    @commands.command(name="iunmute")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_messages=True)
    async def iunmute(self, ctx: "PushieContext", member: discord.Member) -> None:
        """Image unmute a member."""
        assert ctx.guild is not None
        g = ctx.bot.storage.get_guild_sync(ctx.guild.id)
        if not g or not g.imute_role:
            await ctx.err("*No image mute role configured.*")
            return
        imute_role = ctx.guild.get_role(g.imute_role)
        if not imute_role:
            await ctx.err("*Image mute role not found.*")
            return
        try:
            await member.remove_roles(imute_role, reason="Image unmuted")
            await ctx.ok(f"`{Emoji.IMUTE}` *{member.mention} has been image unmuted.*")
        except discord.Forbidden:
            await ctx.err("*I don't have permission to remove the image mute role.*")

    @commands.command(name="runmute")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_roles=True)
    async def runmute(self, ctx: "PushieContext", member: discord.Member) -> None:
        """Reaction unmute a member."""
        assert ctx.guild is not None
        g = ctx.bot.storage.get_guild_sync(ctx.guild.id)
        if not g or not g.rmute_role:
            await ctx.err("*No reaction mute role configured.*")
            return
        rmute_role = ctx.guild.get_role(g.rmute_role)
        if not rmute_role:
            await ctx.err("*Reaction mute role not found.*")
            return
        try:
            await member.remove_roles(rmute_role, reason="Reaction unmuted")
            await ctx.ok(f"`{Emoji.RMUTE}` *{member.mention} has been reaction unmuted.*")
        except discord.Forbidden:
            await ctx.err("*I don't have permission to remove the reaction mute role.*")

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
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.send(
                embed=UI.error("*This command can only be used in a server.*")
            )
        else:
            raise error


async def setup(bot: "Pushie") -> None:
    await bot.add_cog(Moderation(bot))
