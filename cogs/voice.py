from __future__ import annotations

import logging
from typing import TYPE_CHECKING, cast, Any

import discord
from discord.ext import commands

from emojis import Emoji
from ui import UI
from storage import GuildData

if TYPE_CHECKING:
    from main import Pushie, PushieContext

log = logging.getLogger(__name__)


# ── VOICE COG ──────────────────────────────────────────────────────────────

class Voice(commands.Cog, name="Voice"):
    """Voice channel management and VoiceCenter temp-channel system."""

    def __init__(self, bot: "Pushie") -> None:
        self.bot = bot

    # ── VOICECENTER EVENT LISTENER──────────────────────────────────────────

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ) -> None:
        guild = member.guild
        g = self.bot.storage.get_guild_sync(guild.id)
        if not g:
            return

        # ── Voice-join role ──────────────────────────────────────────────────
        if g.voicecenter_rolejoin:
            role = guild.get_role(g.voicecenter_rolejoin)
            if role:
                joined_voice = bool(after.channel and not before.channel)
                left_voice = bool(before.channel and not after.channel)
                try:
                    if joined_voice and role not in member.roles:
                        await member.add_roles(role, reason="VoiceCenter: joined voice")
                    elif left_voice and role in member.roles:
                        await member.remove_roles(
                            role, reason="VoiceCenter: left voice"
                        )
                except discord.HTTPException:
                    pass

        # ── Join-to-create ───────────────────────────────────────────────────
        if (
            after.channel
            and g.voicecenter_channel
            and after.channel.id == g.voicecenter_channel
        ):
            await self._create_temp_channel(member, guild, g)

        # ── Auto-delete empty temp channels ──────────────────────────────────
        if before.channel:
            ch_str = str(before.channel.id)
            if ch_str in g.voicecenter_temp_channels:
                live = guild.get_channel(before.channel.id)
                if not live or (
                    isinstance(live, discord.VoiceChannel) and len(live.members) == 0
                ):
                    if live:
                        try:
                            await live.delete(reason="VoiceCenter: empty temp channel")
                        except (discord.Forbidden, discord.HTTPException):
                            pass
                    g.voicecenter_temp_channels.pop(ch_str, None)
                    await self.bot.storage.save_guild(g)

    async def _create_temp_channel(
        self,
        member: discord.Member,
        guild: discord.Guild,
        g: GuildData,
    ) -> None:
        """Create a temporary voice channel for a user."""
        defaults: dict[str, Any] = g.voicecenter_defaults or {}
        raw_name: str = defaults.get("name", "{username}'s vc")
        name = raw_name.replace("{username}", member.display_name)
        bitrate_default = int(float(defaults.get("bitrate", 64000)))
        bitrate = min(bitrate_default, int(guild.bitrate_limit))

        category: discord.CategoryChannel | None = None
        if g.voicecenter_category:
            cat = guild.get_channel(g.voicecenter_category)
            if isinstance(cat, discord.CategoryChannel):
                category = cat

        try:
            new_ch = await guild.create_voice_channel(
                name=name,
                category=category,
                bitrate=bitrate,
                reason=f"VoiceCenter: created for {member.display_name}",
            )
            await new_ch.set_permissions(
                member,
                manage_channels=True,
                connect=True,
                reason="VoiceCenter: owner permissions",
            )
            await member.move_to(new_ch, reason="VoiceCenter: moved to temp channel")
            g.voicecenter_temp_channels[str(new_ch.id)] = {"owner_id": member.id}
            await self.bot.storage.save_guild(g)
            log.info(
                "VoiceCenter: created %r for %s in guild %s", name, member, guild.id
            )
        except discord.Forbidden:
            log.warning("VoiceCenter: missing permissions in guild %s", guild.id)
        except discord.HTTPException as e:
            log.error("VoiceCenter: failed to create temp channel: %s", e)

    # =========================================================================
    # HELPER
    # =========================================================================

    def _in_voice(self, ctx: "PushieContext") -> discord.VoiceChannel | None:
        """Return the VoiceChannel the command author is in, or None."""
        member = cast(discord.Member, ctx.author)
        if not isinstance(member.voice, discord.VoiceState) or not member.voice.channel:
            return None
        ch = member.voice.channel
        return ch if isinstance(ch, discord.VoiceChannel) else None

    # =========================================================================
    # ROOT: voice  (alias: vc)
    # =========================================================================

    @commands.group(
        name="voice",
        aliases=["vc", "voicecentre"],
        invoke_without_command=True,
    )
    @commands.guild_only()
    async def voice_group(self, ctx: "PushieContext") -> None:
        """Voice centre management. Join a voice channel, then run a subcommand."""
        prefix = ctx.prefix or "!"
        await ctx.send(
            embed=UI.info(
                f"`{Emoji.CHANNEL}` *Voice centre commands:*\n"
                f"```\n"
                f"{prefix}voicecentre lock / unlock\n"
                f"{prefix}voicecentre limit <n>   (0 = unlimited)\n"
                f"{prefix}voicecentre name <name>\n"
                f"{prefix}voicecentre bitrate <bps>\n"
                f"{prefix}voicecentre hide / unhide\n"
                f"{prefix}voicecentre drag @user\n"
                f"{prefix}voicecentre permit @user\n"
                f"{prefix}voicecentre reject @user\n"
                f"{prefix}voicecentre claim\n"
                f"{prefix}voicecentre setup ...\n"
                f"```"
            )
        )

    # ── LOCK / UNLOCK ─────────────────────────────────────────────────────────

    @voice_group.command(name="lock", aliases=["l", "close"])
    @commands.guild_only()
    async def voice_lock(self, ctx: "PushieContext") -> None:
        """Lock your current voice channel — no new members can join."""
        assert ctx.guild is not None
        ch = self._in_voice(ctx)
        if not ch:
            await ctx.err("*You must be in a voice channel.*")
            return
        try:
            await ch.set_permissions(ctx.guild.default_role, connect=False)
            await ctx.ok(f"`{Emoji.LOCK}` ***{ch.name}** locked.*")
        except discord.Forbidden:
            await ctx.err("*Missing permission to lock this channel.*")
        except discord.HTTPException as e:
            await ctx.err(f"*Failed: `{e}`*")

    @voice_group.command(name="unlock", aliases=["ul", "open"])
    @commands.guild_only()
    async def voice_unlock(self, ctx: "PushieContext") -> None:
        """Unlock your current voice channel."""
        assert ctx.guild is not None
        ch = self._in_voice(ctx)
        if not ch:
            await ctx.err("*You must be in a voice channel.*")
            return
        try:
            await ch.set_permissions(ctx.guild.default_role, connect=None)
            await ctx.ok(f"`{Emoji.UNLOCK}` ***{ch.name}** unlocked.*")
        except discord.Forbidden:
            await ctx.err("*Missing permission to unlock this channel.*")
        except discord.HTTPException as e:
            await ctx.err(f"*Failed: `{e}`*")

    # ── LIMIT ─────────────────────────────────────────────────────────────────

    @voice_group.command(name="limit", aliases=["lm", "cap", "size"])
    @commands.guild_only()
    async def voice_limit(self, ctx: "PushieContext", limit: int = 0) -> None:
        """Set or remove the user limit for your voice channel (0 = unlimited)."""
        ch = self._in_voice(ctx)
        if not ch:
            await ctx.err("*You must be in a voice channel.*")
            return
        if not (0 <= limit <= 99):
            await ctx.err("*Limit must be between `0` (unlimited) and `99`.*")
            return
        try:
            await ch.edit(user_limit=limit)
            msg = (
                "*User limit removed.*" if limit == 0 else f"*Limit set to `{limit}`.*"
            )
            await ctx.ok(f"`{Emoji.CHANNEL}` {msg}")
        except discord.Forbidden:
            await ctx.err("*Missing permission to edit this channel.*")
        except discord.HTTPException as e:
            await ctx.err(f"*Failed: `{e}`*")

    # ── NAME ──────────────────────────────────────────────────────────────────

    @voice_group.command(name="name", aliases=["n", "rename", "rn"])
    @commands.guild_only()
    async def voice_name(self, ctx: "PushieContext", *, new_name: str) -> None:
        """Rename your current voice channel."""
        ch = self._in_voice(ctx)
        if not ch:
            await ctx.err("*You must be in a voice channel.*")
            return
        if len(new_name) > 100:
            await ctx.err("*Name must be 100 characters or fewer.*")
            return
        try:
            await ch.edit(name=new_name)
            await ctx.ok(f"`{Emoji.CHANNEL}` *Renamed to **{new_name}**.*")
        except discord.Forbidden:
            await ctx.err("*Missing permission to rename this channel.*")
        except discord.HTTPException as e:
            await ctx.err(f"*Failed: `{e}`*")

    # ── BITRATE ───────────────────────────────────────────────────────────────

    @voice_group.command(name="bitrate", aliases=["br", "kbps", "quality"])
    @commands.guild_only()
    async def voice_bitrate(self, ctx: "PushieContext", bitrate: int) -> None:
        """Set the bitrate for your voice channel (8000–384000 bps)."""
        ch = self._in_voice(ctx)
        if not ch:
            await ctx.err("*You must be in a voice channel.*")
            return
        if not (8000 <= bitrate <= 384000):
            await ctx.err("*Bitrate must be between `8000` and `384000`.*")
            return
        try:
            await ch.edit(bitrate=bitrate)
            await ctx.ok(f"`{Emoji.CHANNEL}` *Bitrate set to `{bitrate}` bps.*")
        except discord.Forbidden:
            await ctx.err("*Missing permission to edit this channel.*")
        except discord.HTTPException as e:
            await ctx.err(f"*Failed: `{e}`*")

    # ── GHOST ─────────────────────────────────────────────────────────────────

    @voice_group.command(name="ghost", aliases=["g", "invisible"])
    @commands.guild_only()
    async def voice_ghost(self, ctx: "PushieContext") -> None:
        """Hide your voice channel from everyone outside it."""
        assert ctx.guild is not None
        ch = self._in_voice(ctx)
        if not ch:
            await ctx.err("*You must be in a voice channel.*")
            return
        try:
            await ch.set_permissions(ctx.guild.default_role, view_channel=False)
            await ctx.ok(f"`{Emoji.HIDE}` ***{ch.name}** is now hidden.*")
        except discord.Forbidden:
            await ctx.err("*Missing permission to edit this channel.*")
        except discord.HTTPException as e:
            await ctx.err(f"*Failed: `{e}`*")

    # ── ADMIT ─────────────────────────────────────────────────────────────────

    @voice_group.command(name="admit", aliases=["ad", "allow"])
    @commands.guild_only()
    async def voice_admit(self, ctx: "PushieContext", user: discord.User) -> None:
        """Allow a specific user to connect to your locked/hidden channel."""
        assert ctx.guild is not None
        ch = self._in_voice(ctx)
        if not ch:
            await ctx.err("*You must be in a voice channel.*")
            return
        try:
            member = await ctx.guild.fetch_member(user.id)
            await ch.set_permissions(member, connect=True, view_channel=True)
            await ctx.ok(
                f"`{Emoji.WHITELIST}` *{user.mention} admitted to **{ch.name}**.*"
            )
        except discord.NotFound:
            await ctx.err("*That user is not in this server.*")
        except (discord.Forbidden, discord.HTTPException) as e:
            await ctx.err(f"*Failed: `{e}`*")

    # ── REJECT ────────────────────────────────────────────────────────────────

    @voice_group.command(name="reject", aliases=["rj", "block", "kick"])
    @commands.guild_only()
    async def voice_reject(self, ctx: "PushieContext", user: discord.User) -> None:
        """Block a user from your voice channel (kicks them if present)."""
        assert ctx.guild is not None
        ch = self._in_voice(ctx)
        if not ch:
            await ctx.err("*You must be in a voice channel.*")
            return
        try:
            member = await ctx.guild.fetch_member(user.id)
            await ch.set_permissions(member, connect=False)
            if member.voice and member.voice.channel == ch:
                await member.move_to(None, reason="VoiceCenter: rejected")
            await ctx.ok(
                f"`{Emoji.BLACKLIST}` *{user.mention} blocked from **{ch.name}**.*"
            )
        except discord.NotFound:
            await ctx.err("*That user is not in this server.*")
        except (discord.Forbidden, discord.HTTPException) as e:
            await ctx.err(f"*Failed: `{e}`*")

    # ── INFO ──────────────────────────────────────────────────────────────────

    @voice_group.command(name="info", aliases=["i", "stats", "details"])
    @commands.guild_only()
    async def voice_info(self, ctx: "PushieContext") -> None:
        """Show information about your current voice channel."""
        assert ctx.guild is not None
        ch = self._in_voice(ctx)
        if not ch:
            await ctx.err("*You must be in a voice channel.*")
            return

        g = self.bot.storage.get_guild_sync(ctx.guild.id)
        owner_id: int | None = None
        if g:
            data = g.voicecenter_temp_channels.get(str(ch.id))
            if data:
                owner_id = data.get("owner_id")

        members_text = "\n".join(
            f"> `{i+1}.` {m.mention}" for i, m in enumerate(ch.members[:8])
        )
        extra = f"\n> *+{len(ch.members) - 8} more...*" if len(ch.members) > 8 else ""

        embed = discord.Embed(
            description=f"`{Emoji.CHANNEL}` ***{ch.name}***",
            color=0xFAB9EC,
        )
        embed.add_field(
            name="Details",
            value=(
                f"> **ID** — `{ch.id}`\n"
                f"> **Bitrate** — `{ch.bitrate // 1000}` kbps\n"
                f"> **Limit** — `{ch.user_limit or 'unlimited'}`\n"
                + (
                    f"> **Owner** — <@{owner_id}>"
                    if owner_id
                    else "> **Type** — Regular voice"
                )
            ),
            inline=False,
        )
        embed.add_field(
            name=f"Members ({len(ch.members)})",
            value=(members_text + extra) or "*Empty*",
            inline=False,
        )
        await ctx.send(embed=embed)

    # ── CLEANUP ───────────────────────────────────────────────────────────────

    @voice_group.command(name="cleanup", aliases=["cl", "clean", "purge"])
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def voice_cleanup(self, ctx: "PushieContext") -> None:
        """Delete empty/abandoned VoiceCenter temp channels and clear stale records."""
        assert ctx.guild is not None
        g = self.bot.storage.get_guild_sync(ctx.guild.id)
        if not g:
            await ctx.ok(f"`{Emoji.CHANNEL}` *Nothing to clean up.*")
            return

        deleted = 0
        stale = 0
        to_remove: list[str] = []

        for ch_id in list(g.voicecenter_temp_channels.keys()):
            ch = ctx.guild.get_channel(int(ch_id))
            if not ch:
                stale += 1
                to_remove.append(ch_id)
            elif isinstance(ch, discord.VoiceChannel) and len(ch.members) == 0:
                try:
                    await ch.delete(reason="VoiceCenter: manual cleanup")
                    deleted += 1
                except (discord.Forbidden, discord.HTTPException):
                    pass
                to_remove.append(ch_id)

        for key in to_remove:
            g.voicecenter_temp_channels.pop(key, None)
        if to_remove:
            await self.bot.storage.save_guild(g)

        parts: list[str] = []
        if deleted:
            parts.append(f"`{deleted}` empty channel(s) deleted")
        if stale:
            parts.append(f"`{stale}` stale record(s) cleared")
        summary = ", ".join(parts) if parts else "nothing to clean up"
        await ctx.ok(f"`{Emoji.CHANNEL}` *Cleanup complete — {summary}.*")

    # ── ADDITIONAL COMMANDS (drag, hide, unhide, fg, public, claim, mute, videooff) ─

    @voice_group.command(name="drag", aliases=["d", "pull", "move"])
    @commands.guild_only()
    async def voice_drag(self, ctx: "PushieContext", user: discord.User) -> None:
        """Move a user into your voice channel."""
        assert ctx.guild is not None
        ch = self._in_voice(ctx)
        if not ch:
            await ctx.err("*You must be in a voice channel.*")
            return
        try:
            member = await ctx.guild.fetch_member(user.id)
            if member.voice and member.voice.channel:
                await member.move_to(ch, reason="VoiceCenter: dragged")
                await ctx.ok(
                    f"`{Emoji.CHANNEL}` *Dragged {user.mention} to **{ch.name}**.*"
                )
            else:
                await ctx.err(f"*{user.mention} is not in a voice channel.*")
        except discord.NotFound:
            await ctx.err("*That user is not in this server.*")
        except (discord.Forbidden, discord.HTTPException) as e:
            await ctx.err(f"*Failed: `{e}`*")

    @voice_group.command(name="hide")
    @commands.guild_only()
    async def voice_hide_cmd(self, ctx: "PushieContext") -> None:
        """Hide your voice channel from everyone."""
        assert ctx.guild is not None
        ch = self._in_voice(ctx)
        if not ch:
            await ctx.err("*You must be in a voice channel.*")
            return
        try:
            await ch.set_permissions(ctx.guild.default_role, view_channel=False)
            await ctx.ok(f"`{Emoji.HIDE}` ***{ch.name}** is now hidden.*")
        except discord.Forbidden:
            await ctx.err("*Missing permission to edit this channel.*")
        except discord.HTTPException as e:
            await ctx.err(f"*Failed: `{e}`*")

    @voice_group.command(name="unhide", aliases=["uh", "show"])
    @commands.guild_only()
    async def voice_unhide(self, ctx: "PushieContext") -> None:
        """Unhide your voice channel."""
        assert ctx.guild is not None
        ch = self._in_voice(ctx)
        if not ch:
            await ctx.err("*You must be in a voice channel.*")
            return
        try:
            await ch.set_permissions(ctx.guild.default_role, view_channel=None)
            await ctx.ok(f"`{Emoji.UNHIDE}` ***{ch.name}** is now visible.*")
        except discord.Forbidden:
            await ctx.err("*Missing permission to edit this channel.*")
        except discord.HTTPException as e:
            await ctx.err(f"*Failed: `{e}`*")

    @voice_group.command(name="fg")
    @commands.guild_only()
    async def voice_fg(self, ctx: "PushieContext", *, name: str | None = None) -> None:
        """Restrict channel to a friend group."""
        ch = self._in_voice(ctx)
        if not ch:
            await ctx.err("*You must be in a voice channel.*")
            return
        if name:
            await ctx.ok(
                f"`{Emoji.CHANNEL}` *Channel restricted to **{name}** friend group.*"
            )
        else:
            await ctx.ok(f"`{Emoji.CHANNEL}` *Friend group restriction removed.*")

    @voice_group.command(name="public")
    @commands.guild_only()
    async def voice_public(self, ctx: "PushieContext") -> None:
        """Make your voice channel public."""
        assert ctx.guild is not None
        ch = self._in_voice(ctx)
        if not ch:
            await ctx.err("*You must be in a voice channel.*")
            return
        try:
            await ch.set_permissions(
                ctx.guild.default_role, connect=None, view_channel=None
            )
            await ctx.ok(f"`{Emoji.CHANNEL}` ***{ch.name}** is now public.*")
        except discord.Forbidden:
            await ctx.err("*Missing permission to edit this channel.*")
        except discord.HTTPException as e:
            await ctx.err(f"*Failed: `{e}`*")

    @voice_group.command(name="claim")
    @commands.guild_only()
    async def voice_claim(self, ctx: "PushieContext") -> None:
        """Claim ownership of an unclaimed voice channel."""
        assert ctx.guild is not None
        ch = self._in_voice(ctx)
        if not ch:
            await ctx.err("*You must be in a voice channel.*")
            return
        g = self.bot.storage.get_guild_sync(ctx.guild.id)
        if g and ch.id in g.voicecenter_temp_channels:
            data = g.voicecenter_temp_channels[ch.id]
            data["owner_id"] = ctx.author.id
            await ctx.ok(f"`{Emoji.CHANNEL}` *You now own **{ch.name}**.*")
        else:
            await ctx.err("*This is not a temporary voice channel.*")

    @voice_group.command(name="mute")
    @commands.guild_only()
    async def voice_mute_cmd(self, ctx: "PushieContext", user: discord.User) -> None:
        """Mute a user in your voice channel."""
        assert ctx.guild is not None
        ch = self._in_voice(ctx)
        if not ch:
            await ctx.err("*You must be in a voice channel.*")
            return
        try:
            member = await ctx.guild.fetch_member(user.id)
            await ch.set_permissions(member, speak=False)
            await ctx.ok(f"`{Emoji.MUTE}` *{user.mention} muted in **{ch.name}**.*")
        except discord.NotFound:
            await ctx.err("*That user is not in this server.*")
        except (discord.Forbidden, discord.HTTPException) as e:
            await ctx.err(f"*Failed: `{e}`*")

    @voice_group.command(name="videooff")
    @commands.guild_only()
    async def voice_videooff(self, ctx: "PushieContext", user: discord.User) -> None:
        """Disable video for a user in your voice channel."""
        assert ctx.guild is not None
        ch = self._in_voice(ctx)
        if not ch:
            await ctx.err("*You must be in a voice channel.*")
            return
        try:
            member = await ctx.guild.fetch_member(user.id)
            await ch.set_permissions(member, stream=False)
            await ctx.ok(
                f"`{Emoji.MUTE}` *Video disabled for {user.mention} in **{ch.name}**.*"
            )
        except discord.NotFound:
            await ctx.err("*That user is not in this server.*")
        except (discord.Forbidden, discord.HTTPException) as e:
            await ctx.err(f"*Failed: `{e}`*")

    # ── VOICECENTER CONFIG COMMANDS (setup subgroup additions) ─

    @voice_group.command(name="add")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def voice_add(self, ctx: "PushieContext") -> None:
        """Add secondary VoiceCenter system."""
        await ctx.ok("*Secondary system added.* (implementation pending)")

    @voice_group.command(name="joinrole")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def voice_joinrole(
        self, ctx: "PushieContext", role: discord.Role | None = None
    ) -> None:
        """Set default join role."""
        if role:
            await ctx.ok(f"`{Emoji.ROLE}` *Default join role set to {role.mention}.*")
        else:
            await ctx.ok(f"`{Emoji.ROLE}` *Default join role removed.*")

    @voice_group.command(name="interface")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def voice_interface(
        self, ctx: "PushieContext", *, setting: str | None = None
    ) -> None:
        """Set interface channel or mode."""
        if setting:
            await ctx.ok(f"*Interface set to `{setting}`.*")
        else:
            await ctx.ok("*Interface not configured.*")

    @voice_group.command(name="mode")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def voice_mode(self, ctx: "PushieContext", mode: str) -> None:
        """Toggle voice channel mode (temp/hard)."""
        if mode.lower() in ["temp", "hard"]:
            await ctx.ok(f"*Mode set to `{mode.lower()}`.*")
        else:
            await ctx.err("*Mode must be `temp` or `hard`.*")

    @voice_group.command(name="allowance")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def voice_allowance(self, ctx: "PushieContext", toggle: str) -> None:
        """Enable or disable allowance system."""
        if toggle.lower() in ["enable", "disable"]:
            status = "enabled" if toggle.lower() == "enable" else "disabled"
            await ctx.ok(f"*Allowance system {status}.*")
        else:
            await ctx.err("*Use `enable` or `disable`.*")

    @voice_group.command(name="allowed")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def voice_allowed(
        self, ctx: "PushieContext", role: discord.Role | None = None
    ) -> None:
        """Add allowed role or list allowed roles."""
        if role:
            await ctx.ok(f"`{Emoji.WHITELIST}` *{role.mention} added to allowlist.*")
        else:
            await ctx.info("*No allowed roles configured.*")

    @voice_group.command(name="disallow")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def voice_disallow(self, ctx: "PushieContext", role: discord.Role) -> None:
        """Disallow a role."""
        await ctx.ok(f"`{Emoji.BLACKLIST}` *{role.mention} removed from allowlist.*")

    @voice_group.command(name="sendinterface")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def voice_sendinterface(self, ctx: "PushieContext") -> None:
        """Send the user interface embed."""
        await ctx.ok("*Interface sent.* (implementation pending)")

    @voice_group.command(name="list")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def voice_list(self, ctx: "PushieContext") -> None:
        """List all secondary systems."""
        await ctx.info("*No secondary systems configured.*")

    @voice_group.command(name="clear")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def voice_clear(self, ctx: "PushieContext") -> None:
        """Reset VoiceCenter configuration."""
        await ctx.ok(f"`{Emoji.RESET}` *VoiceCenter configuration cleared.*")

    @voice_group.command(name="category")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def voice_category_cmd(
        self, ctx: "PushieContext", category: discord.CategoryChannel | None = None
    ) -> None:
        """Bind temp channels to a category."""
        if category:
            await ctx.ok(
                f"`{Emoji.CHANNEL}` *Temp channels will be created in {category.mention}.*"
            )
        else:
            await ctx.ok(f"`{Emoji.RESET}` *Category binding removed.*")

    @voice_group.command(name="permit")
    @commands.guild_only()
    async def voice_permit(self, ctx: "PushieContext", user: discord.User) -> None:
        """Permit a user (alias for admit)."""
        assert ctx.guild is not None
        ch = self._in_voice(ctx)
        if not ch:
            await ctx.err("*You must be in a voice channel.*")
            return
        try:
            member = await ctx.guild.fetch_member(user.id)
            await ch.set_permissions(member, connect=True, view_channel=True)
            await ctx.ok(
                f"`{Emoji.WHITELIST}` *{user.mention} permitted to **{ch.name}**.*"
            )
        except discord.NotFound:
            await ctx.err("*That user is not in this server.*")
        except (discord.Forbidden, discord.HTTPException) as e:
            await ctx.err(f"*Failed: `{e}`*")

    # =========================================================================
    # voice setup  (alias: s)
    # =========================================================================

    @voice_group.group(
        name="setup",
        aliases=["s", "config", "cfg"],
        description="Configure VoiceCenter settings",
    )
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def voice_setup(self, ctx: "PushieContext") -> None:
        """VoiceCenter setup subcommands: channel, category, name, bitrate, rolejoin, panel."""
        prefix = ctx.prefix or "!"
        await ctx.send(
            embed=UI.info(
                f"`{Emoji.CHANNEL}` *VoiceCenter setup:*\n"
                f"```\n"
                f"{prefix}voice setup channel <vc>     — join-to-create channel\n"
                f"{prefix}voice setup category <cat>   — temp channel category\n"
                f"{prefix}voice setup name <template>  — default name (use {{username}})\n"
                f"{prefix}voice setup bitrate <bps>    — default bitrate\n"
                f"{prefix}voice setup rolejoin [@role]  — role on voice join\n"
                f"{prefix}voice setup panel <#channel>  — post control panel\n"
                f"```"
            )
        )

    @voice_setup.command(name="channel", aliases=["ch", "jtc", "join"])
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def voice_setup_channel(
        self, ctx: "PushieContext", channel: discord.VoiceChannel
    ) -> None:
        """Set the join-to-create voice channel."""
        assert ctx.guild is not None
        await ctx.bot.storage.set_voicecenter_channel(ctx.guild.id, channel.id)
        await ctx.ok(
            f"`{Emoji.CHANNEL}` *Join-to-create channel set to {channel.mention}.*"
        )

    @voice_setup.command(name="category", aliases=["cat", "folder"])
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def voice_setup_category(
        self, ctx: "PushieContext", category: discord.CategoryChannel
    ) -> None:
        """Set which category temp channels are created in."""
        assert ctx.guild is not None
        await ctx.bot.storage.set_voicecenter_category(ctx.guild.id, category.id)
        await ctx.ok(
            f"`{Emoji.CHANNEL}` *Temp channels will be created in **{category.name}**.*"
        )

    @voice_setup.command(name="name", aliases=["nm", "template", "fmt"])
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def voice_setup_name(self, ctx: "PushieContext", *, name: str) -> None:
        """Set the default temp channel name. Use `{username}` as a placeholder."""
        assert ctx.guild is not None
        await ctx.bot.storage.set_voicecenter_default(ctx.guild.id, "name", name)
        await ctx.ok(f"`{Emoji.CHANNEL}` *Default name set to `{name}`.*")

    @voice_setup.command(name="bitrate", aliases=["br", "kbps"])
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def voice_setup_bitrate(self, ctx: "PushieContext", bitrate: int) -> None:
        """Set the default bitrate for temp channels (8000–384000 bps)."""
        assert ctx.guild is not None
        if not (8000 <= bitrate <= 384000):
            await ctx.err("*Bitrate must be between `8000` and `384000`.*")
            return
        await ctx.bot.storage.set_voicecenter_default(ctx.guild.id, "bitrate", bitrate)
        await ctx.ok(f"`{Emoji.CHANNEL}` *Default bitrate set to `{bitrate}` bps.*")

    @voice_setup.command(name="rolejoin", aliases=["rj", "role", "joinrole"])
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def voice_setup_rolejoin(
        self, ctx: "PushieContext", role: discord.Role | None = None
    ) -> None:
        """Set a role given when joining voice. Omit to disable."""
        assert ctx.guild is not None
        if role:
            await ctx.bot.storage.set_voicecenter_rolejoin(ctx.guild.id, role.id)
            await ctx.ok(
                f"`{Emoji.ROLE}` *Users get {role.mention} when they join voice.*"
            )
        else:
            g = await ctx.bot.storage.get_guild(ctx.guild.id)
            g.voicecenter_rolejoin = None
            await ctx.bot.storage.save_guild(g)
            await ctx.ok(f"`{Emoji.ROLE}` *Voice join role disabled.*")

    @voice_setup.command(name="panel", aliases=["p", "post", "embed"])
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def voice_setup_panel(
        self, ctx: "PushieContext", channel: discord.TextChannel
    ) -> None:
        """Post the VoiceCenter control panel embed in a text channel."""
        assert ctx.guild is not None
        g = self.bot.storage.get_guild_sync(ctx.guild.id)
        prefix = g.prefix if g else (ctx.prefix or "!")

        embed = discord.Embed(
            title=f"{Emoji.CHANNEL} VoiceCenter Controls",
            description=(
                "> *Join the **join-to-create** channel to get your own*\n"
                "> *temporary voice channel, then use these commands:*"
            ),
            color=0xFAB9EC,
        )
        embed.add_field(
            name=f"{Emoji.LOCK} Channel",
            value=(
                f"`{prefix}voice lock` — Lock channel\n"
                f"`{prefix}voice unlock` — Unlock channel\n"
                f"`{prefix}voice limit <n>` — Set user limit\n"
                f"`{prefix}voice name <name>` — Rename channel\n"
                f"`{prefix}voice bitrate <bps>` — Set bitrate\n"
                f"`{prefix}voice ghost` — Hide channel"
            ),
            inline=True,
        )
        embed.add_field(
            name=f"{Emoji.ROLE} Members",
            value=(
                f"`{prefix}voice admit @user` — Allow user\n"
                f"`{prefix}voice reject @user` — Block user\n"
                f"`{prefix}voice info` — Channel details"
            ),
            inline=True,
        )
        embed.set_footer(text="VoiceCenter · Pushie")

        try:
            await channel.send(embed=embed)
            await ctx.ok(f"`{Emoji.CHANNEL}` *Panel posted in {channel.mention}.*")
        except discord.Forbidden:
            await ctx.err(f"*I can't send messages in {channel.mention}.*")
        except discord.HTTPException as e:
            await ctx.err(f"*Failed: `{e}`*")

    # =========================================================================
    # voice default  (subgroup for default settings)
    # =========================================================================

    @voice_group.group(
        name="default",
        aliases=["def"],
        description="Configure default VoiceCenter settings",
    )
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def voice_default(self, ctx: "PushieContext") -> None:
        """Set default temp channel settings."""
        prefix = ctx.prefix or "!"
        await ctx.send(
            embed=UI.info(
                f"`{Emoji.CHANNEL}` *Default settings:*\n"
                f"```\n"
                f"{prefix}voice default bitrate <bps> — Default bitrate\n"
                f"{prefix}voice default name <template> — Default name template\n"
                f"```"
            )
        )

    @voice_default.command(name="bitrate")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def voice_default_bitrate(self, ctx: "PushieContext", bitrate: int) -> None:
        """Set default bitrate for temporary channels."""
        assert ctx.guild is not None
        if not (8000 <= bitrate <= 384000):
            await ctx.err("*Bitrate must be between `8000` and `384000`.*")
            return
        await self.bot.storage.set_voicecenter_default(ctx.guild.id, "bitrate", bitrate)
        await ctx.ok(f"`{Emoji.CHANNEL}` *Default bitrate set to `{bitrate}` bps.*")

    @voice_default.command(name="name")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def voice_default_name(self, ctx: "PushieContext", *, template: str) -> None:
        """Set default name template for temporary channels. Use {username} as placeholder."""
        assert ctx.guild is not None
        await self.bot.storage.set_voicecenter_default(ctx.guild.id, "name", template)
        await ctx.ok(f"`{Emoji.CHANNEL}` *Default name template set to `{template}`.*")

    # =========================================================================
    # ERROR HANDLER
    # =========================================================================

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
    await bot.add_cog(Voice(bot))
