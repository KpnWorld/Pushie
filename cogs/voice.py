from __future__ import annotations

import logging
from typing import TYPE_CHECKING, cast

import discord
from discord.ext import commands

from emojis import Emoji
from ui import UI

if TYPE_CHECKING:
    from main import Pushie, PushieContext

log = logging.getLogger(__name__)


class Voice(commands.Cog, name="Voice"):
    """Voice channel management and VoiceCenter system."""

    def __init__(self, bot: "Pushie") -> None:
        self.bot = bot

    # =========================================================================
    # VOICECENTER EVENT — join-to-create, auto-delete, voice-join role
    # =========================================================================

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
                joined_voice = after.channel and not before.channel
                left_voice = before.channel and not after.channel
                try:
                    if joined_voice and role not in member.roles:
                        await member.add_roles(role, reason="VoiceCenter: joined voice")
                    elif left_voice and role in member.roles:
                        await member.remove_roles(role, reason="VoiceCenter: left voice")
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
            ch_id_str = str(before.channel.id)
            if ch_id_str in g.voicecenter_temp_channels:
                live_ch = guild.get_channel(before.channel.id)
                if not live_ch or (
                    isinstance(live_ch, discord.VoiceChannel)
                    and len(live_ch.members) == 0
                ):
                    if live_ch:
                        try:
                            await live_ch.delete(
                                reason="VoiceCenter: empty temp channel"
                            )
                        except (discord.Forbidden, discord.HTTPException):
                            pass
                    g.voicecenter_temp_channels.pop(ch_id_str, None)
                    await self.bot.storage.save_guild(g)

    async def _create_temp_channel(
        self,
        member: discord.Member,
        guild: discord.Guild,
        g: "GuildData",  # type: ignore[name-defined]
    ) -> None:
        """Create a temporary voice channel and move the member into it."""
        defaults = g.voicecenter_defaults or {}
        raw_name: str = defaults.get("name", "{username}'s vc")
        name = raw_name.replace("{username}", member.display_name)
        bitrate = int(defaults.get("bitrate", 64000))
        bitrate = min(bitrate, guild.bitrate_limit)

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
                reason="VoiceCenter: channel owner permissions",
            )
            await member.move_to(new_ch, reason="VoiceCenter: moved to temp channel")

            g.voicecenter_temp_channels[str(new_ch.id)] = {
                "owner_id": member.id,
                "name": name,
            }
            await self.bot.storage.save_guild(g)
            log.info(
                "VoiceCenter: created %r (id=%s) for %s in guild %s",
                name,
                new_ch.id,
                member,
                guild.id,
            )
        except discord.Forbidden:
            log.warning(
                "VoiceCenter: missing permissions in guild %s — cannot create channel",
                guild.id,
            )
        except discord.HTTPException as e:
            log.error("VoiceCenter: failed to create temp channel: %s", e)

    # =========================================================================
    # VOICE-SETUP SUBCOMMANDS
    # =========================================================================

    @commands.hybrid_group(
        name="voice-setup", description="Configure VoiceCenter (temp voice channels)"
    )
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def voice_setup(self, ctx: "PushieContext") -> None:
        """VoiceCenter configuration commands."""
        pass

    @voice_setup.command(
        name="channel", description="Set the join-to-create voice channel"
    )
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def voice_setup_channel(
        self, ctx: "PushieContext", channel: discord.VoiceChannel
    ) -> None:
        """Set which voice channel users join to create temporary channels."""
        assert ctx.guild is not None
        await ctx.bot.storage.set_voicecenter_channel(ctx.guild.id, channel.id)
        await ctx.ok(
            f"`{Emoji.CHANNEL}` *Join-to-create channel set to {channel.mention}.*"
        )

    @voice_setup.command(
        name="category", description="Set category for temporary voice channels"
    )
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def setup_category(
        self, ctx: "PushieContext", category: discord.CategoryChannel
    ) -> None:
        """Set which category temporary voice channels are created in."""
        assert ctx.guild is not None
        await ctx.bot.storage.set_voicecenter_category(ctx.guild.id, category.id)
        await ctx.ok(
            f"`{Emoji.CHANNEL}` *Temp channels will be created in **{category.name}**.*"
        )

    @voice_setup.command(
        name="name",
        description="Default name for temp channels. Use {username} as placeholder.",
    )
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def setup_name(self, ctx: "PushieContext", *, name: str) -> None:
        """Set the default name format. `{username}` is replaced with the creator's display name."""
        assert ctx.guild is not None
        await ctx.bot.storage.set_voicecenter_default(ctx.guild.id, "name", name)
        await ctx.ok(f"`{Emoji.CHANNEL}` *Temp channel name set to `{name}`.*")

    @voice_setup.command(
        name="bitrate", description="Default bitrate (bps) for temp channels"
    )
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def setup_bitrate(self, ctx: "PushieContext", bitrate: int) -> None:
        """Set the default bitrate (8000–384000 bps) for temporary voice channels."""
        if bitrate < 8000 or bitrate > 384000:
            await ctx.err("*Bitrate must be between `8000` and `384000`.*")
            return
        assert ctx.guild is not None
        await ctx.bot.storage.set_voicecenter_default(ctx.guild.id, "bitrate", bitrate)
        await ctx.ok(f"`{Emoji.CHANNEL}` *Default bitrate set to `{bitrate}` bps.*")

    @voice_setup.command(
        name="rolejoin", description="Role given when joining any voice channel"
    )
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def setup_rolejoin(
        self, ctx: "PushieContext", role: discord.Role | None = None
    ) -> None:
        """Assign a role when users join voice; omit `role` to disable."""
        assert ctx.guild is not None
        if role:
            await ctx.bot.storage.set_voicecenter_rolejoin(ctx.guild.id, role.id)
            await ctx.ok(
                f"`{Emoji.ROLE}` *Users will receive {role.mention} when joining voice.*"
            )
        else:
            g = await ctx.bot.storage.get_guild(ctx.guild.id)
            g.voicecenter_rolejoin = None
            await ctx.bot.storage.save_guild(g)
            await ctx.ok(f"`{Emoji.ROLE}` *Voice join role disabled.*")

    @voice_setup.command(
        name="panel", description="Post VoiceCenter control panel in a text channel"
    )
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def setup_panel(
        self, ctx: "PushieContext", channel: discord.TextChannel
    ) -> None:
        """Post the VoiceCenter control panel embed in a text channel."""
        assert ctx.guild is not None
        g = self.bot.storage.get_guild_sync(ctx.guild.id)
        prefix = g.prefix if g else "!"

        embed = discord.Embed(
            title=f"{Emoji.CHANNEL} VoiceCenter Controls",
            description=(
                "> *Join the **join-to-create** channel to get your own*\n"
                "> *temporary voice channel. Use these commands to manage it.*"
            ),
            color=0xFAB9EC,
        )
        embed.add_field(
            name=f"{Emoji.LOCK} Channel",
            value=(
                f"`{prefix}voice-lock` — Lock your channel\n"
                f"`{prefix}voice-unlock` — Unlock your channel\n"
                f"`{prefix}voice-limit <n>` — Set user limit (0 = unlimited)\n"
                f"`{prefix}voice-name <name>` — Rename your channel\n"
                f"`{prefix}voice-bitrate <bps>` — Set bitrate\n"
                f"`{prefix}ghost` — Hide channel from others"
            ),
            inline=True,
        )
        embed.add_field(
            name=f"{Emoji.ROLE} Members",
            value=(
                f"`{prefix}admit @user` — Allow a user to join\n"
                f"`{prefix}reject @user` — Block a user from joining\n"
                f"`{prefix}info` — Show channel info"
            ),
            inline=True,
        )
        embed.set_footer(text="VoiceCenter · Pushie")

        try:
            await channel.send(embed=embed)
            await ctx.ok(
                f"`{Emoji.CHANNEL}` *Control panel posted in {channel.mention}.*"
            )
        except discord.Forbidden:
            await ctx.err(f"*I can't send messages in {channel.mention}.*")
        except discord.HTTPException as e:
            await ctx.err(f"*Failed to post panel: `{e}`*")

    # =========================================================================
    # CLEANUP
    # =========================================================================

    @commands.hybrid_command(
        name="cleanup", description="Delete empty/abandoned VoiceCenter channels"
    )
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def cleanup(self, ctx: "PushieContext") -> None:
        """Delete all empty tracked temp channels and clear stale records."""
        assert ctx.guild is not None
        g = self.bot.storage.get_guild_sync(ctx.guild.id)
        if not g:
            await ctx.ok(f"`{Emoji.CHANNEL}` *Nothing to clean up.*")
            return

        deleted = 0
        stale = 0
        to_remove: list[str] = []

        for ch_id_str in list(g.voicecenter_temp_channels.keys()):
            ch = ctx.guild.get_channel(int(ch_id_str))
            if not ch:
                stale += 1
                to_remove.append(ch_id_str)
            elif isinstance(ch, discord.VoiceChannel) and len(ch.members) == 0:
                try:
                    await ch.delete(reason="VoiceCenter: manual cleanup")
                    deleted += 1
                except (discord.Forbidden, discord.HTTPException):
                    pass
                to_remove.append(ch_id_str)

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

    # =========================================================================
    # CHANNEL CONTROLS (owner / mod)
    # =========================================================================

    def _get_voice_channel(
        self, ctx: "PushieContext"
    ) -> discord.VoiceChannel | None:
        """Return the VoiceChannel the author is currently in, or None."""
        author = cast(discord.Member, ctx.author)
        if not isinstance(author.voice, discord.VoiceState) or not author.voice.channel:
            return None
        ch = author.voice.channel
        return ch if isinstance(ch, discord.VoiceChannel) else None

    @commands.hybrid_command(
        name="voice-lock", description="Lock your current voice channel"
    )
    @commands.guild_only()
    async def voice_lock(self, ctx: "PushieContext") -> None:
        """Lock your current voice channel — no new members can join."""
        assert ctx.guild is not None
        channel = self._get_voice_channel(ctx)
        if not channel:
            await ctx.err("*You must be in a voice channel.*")
            return
        try:
            await channel.set_permissions(ctx.guild.default_role, connect=False)
            await ctx.ok(f"`{Emoji.LOCK}` ***{channel.name}** has been locked.*")
        except discord.Forbidden:
            await ctx.err("*I don't have permission to lock this channel.*")
        except discord.HTTPException as e:
            await ctx.err(f"*Failed to lock channel: `{e}`*")

    @commands.hybrid_command(
        name="voice-unlock", description="Unlock your current voice channel"
    )
    @commands.guild_only()
    async def voice_unlock(self, ctx: "PushieContext") -> None:
        """Unlock your current voice channel."""
        assert ctx.guild is not None
        channel = self._get_voice_channel(ctx)
        if not channel:
            await ctx.err("*You must be in a voice channel.*")
            return
        try:
            await channel.set_permissions(ctx.guild.default_role, connect=None)
            await ctx.ok(f"`{Emoji.UNLOCK}` ***{channel.name}** has been unlocked.*")
        except discord.Forbidden:
            await ctx.err("*I don't have permission to unlock this channel.*")
        except discord.HTTPException as e:
            await ctx.err(f"*Failed to unlock channel: `{e}`*")

    @commands.hybrid_command(
        name="voice-limit", description="Set user limit for your voice channel (0 = off)"
    )
    @commands.guild_only()
    async def voice_limit(self, ctx: "PushieContext", limit: int = 0) -> None:
        """Set or remove the user limit for your current voice channel."""
        channel = self._get_voice_channel(ctx)
        if not channel:
            await ctx.err("*You must be in a voice channel.*")
            return
        if limit < 0 or limit > 99:
            await ctx.err("*Limit must be between `0` (unlimited) and `99`.*")
            return
        try:
            await channel.edit(user_limit=limit)
            msg = "*User limit removed.*" if limit == 0 else f"*User limit set to `{limit}`.*"
            await ctx.ok(f"`{Emoji.CHANNEL}` {msg}")
        except discord.Forbidden:
            await ctx.err("*I don't have permission to edit this channel.*")
        except discord.HTTPException as e:
            await ctx.err(f"*Failed to set limit: `{e}`*")

    @commands.hybrid_command(
        name="voice-name", description="Rename your current voice channel"
    )
    @commands.guild_only()
    async def voice_name(self, ctx: "PushieContext", *, new_name: str) -> None:
        """Rename your current voice channel."""
        channel = self._get_voice_channel(ctx)
        if not channel:
            await ctx.err("*You must be in a voice channel.*")
            return
        if len(new_name) > 100:
            await ctx.err("*Channel name must be 100 characters or less.*")
            return
        try:
            await channel.edit(name=new_name)
            await ctx.ok(f"`{Emoji.CHANNEL}` *Renamed to **{new_name}**.*")
        except discord.Forbidden:
            await ctx.err("*I don't have permission to rename this channel.*")
        except discord.HTTPException as e:
            await ctx.err(f"*Failed to rename: `{e}`*")

    @commands.hybrid_command(
        name="voice-bitrate", description="Set bitrate for your voice channel"
    )
    @commands.guild_only()
    async def voice_bitrate(self, ctx: "PushieContext", bitrate: int) -> None:
        """Set the bitrate for your current voice channel."""
        channel = self._get_voice_channel(ctx)
        if not channel:
            await ctx.err("*You must be in a voice channel.*")
            return
        if bitrate < 8000 or bitrate > 384000:
            await ctx.err("*Bitrate must be between `8000` and `384000`.*")
            return
        try:
            await channel.edit(bitrate=bitrate)
            await ctx.ok(f"`{Emoji.CHANNEL}` *Bitrate set to `{bitrate}` bps.*")
        except discord.Forbidden:
            await ctx.err("*I don't have permission to edit this channel.*")
        except discord.HTTPException as e:
            await ctx.err(f"*Failed to set bitrate: `{e}`*")

    @commands.hybrid_command(
        name="ghost", description="Hide your voice channel from non-members"
    )
    @commands.guild_only()
    async def ghost(self, ctx: "PushieContext") -> None:
        """Make your current voice channel invisible to everyone outside it."""
        assert ctx.guild is not None
        channel = self._get_voice_channel(ctx)
        if not channel:
            await ctx.err("*You must be in a voice channel.*")
            return
        try:
            await channel.set_permissions(ctx.guild.default_role, view_channel=False)
            await ctx.ok(f"`{Emoji.HIDE}` ***{channel.name}** is now hidden.*")
        except discord.Forbidden:
            await ctx.err("*I don't have permission to edit this channel.*")
        except discord.HTTPException as e:
            await ctx.err(f"*Failed to hide channel: `{e}`*")

    @commands.hybrid_command(
        name="admit", description="Admit a user to a locked/hidden voice channel"
    )
    @commands.guild_only()
    async def admit(self, ctx: "PushieContext", user: discord.User) -> None:
        """Allow a specific user to connect to your locked or hidden voice channel."""
        assert ctx.guild is not None
        channel = self._get_voice_channel(ctx)
        if not channel:
            await ctx.err("*You must be in a voice channel.*")
            return
        try:
            member = await ctx.guild.fetch_member(user.id)
            await channel.set_permissions(member, connect=True, view_channel=True)
            await ctx.ok(
                f"`{Emoji.WHITELIST}` *{user.mention} admitted to **{channel.name}**.*"
            )
        except discord.NotFound:
            await ctx.err("*That user is not in this server.*")
        except (discord.Forbidden, discord.HTTPException) as e:
            await ctx.err(f"*Failed to admit user: `{e}`*")

    @commands.hybrid_command(
        name="reject", description="Block a user from your voice channel"
    )
    @commands.guild_only()
    async def reject(self, ctx: "PushieContext", user: discord.User) -> None:
        """Prevent a specific user from joining your voice channel."""
        assert ctx.guild is not None
        channel = self._get_voice_channel(ctx)
        if not channel:
            await ctx.err("*You must be in a voice channel.*")
            return
        try:
            member = await ctx.guild.fetch_member(user.id)
            await channel.set_permissions(member, connect=False)
            if member.voice and member.voice.channel == channel:
                await member.move_to(None, reason="VoiceCenter: rejected from channel")
            await ctx.ok(
                f"`{Emoji.BLACKLIST}` *{user.mention} blocked from **{channel.name}**.*"
            )
        except discord.NotFound:
            await ctx.err("*That user is not in this server.*")
        except (discord.Forbidden, discord.HTTPException) as e:
            await ctx.err(f"*Failed to block user: `{e}`*")

    @commands.hybrid_command(
        name="info", description="Show info about your current voice channel"
    )
    @commands.guild_only()
    async def info(self, ctx: "PushieContext") -> None:
        """Show information about your current voice channel."""
        assert ctx.guild is not None
        channel = self._get_voice_channel(ctx)
        if not channel:
            await ctx.err("*You must be in a voice channel.*")
            return

        g = self.bot.storage.get_guild_sync(ctx.guild.id)
        owner_id: int | None = None
        if g:
            data = g.voicecenter_temp_channels.get(str(channel.id))
            if data:
                owner_id = data.get("owner_id")

        members_text = "\n".join(
            f"> `{i+1}.` {m.mention}" for i, m in enumerate(channel.members[:8])
        )
        extra = (
            f"\n> *+{len(channel.members) - 8} more...*"
            if len(channel.members) > 8
            else ""
        )

        embed = discord.Embed(
            description=f"`{Emoji.CHANNEL}` ***{channel.name}***",
            color=0xFAB9EC,
        )
        embed.add_field(
            name="Channel Info",
            value=(
                f"> **ID** — `{channel.id}`\n"
                f"> **Bitrate** — `{channel.bitrate // 1000}` kbps\n"
                f"> **Limit** — `{channel.user_limit or 'unlimited'}`\n"
                + (
                    f"> **Owner** — <@{owner_id}>"
                    if owner_id
                    else f"> **Type** — Regular voice"
                )
            ),
            inline=False,
        )
        embed.add_field(
            name=f"Members ({len(channel.members)})",
            value=(members_text + extra) or "*No members.*",
            inline=False,
        )
        await ctx.send(embed=embed)

    # =========================================================================
    # ERROR HANDLER
    # =========================================================================

    async def cog_command_error(self, ctx: commands.Context, error: Exception) -> None:
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
            await ctx.send(embed=UI.error("*This command can only be used in a server.*"))
        else:
            raise error


async def setup(bot: "Pushie") -> None:
    await bot.add_cog(Voice(bot))
