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
        if ctx.guild is None:
            return
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
        if ctx.guild is None:
            return
        await ctx.bot.storage.set_voicecenter_category(ctx.guild.id, category.id)
        await ctx.ok(
            f"`{Emoji.CHANNEL}` *Temp channels will be created in **{category.name}**.*"
        )

    @voice_setup.command(
        name="name", description="Set default name for temporary channels"
    )
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def setup_name(self, ctx: "PushieContext", *, name: str) -> None:
        """Set the default name format for temporary voice channels."""
        if ctx.guild is None:
            return
        await ctx.bot.storage.set_voicecenter_default(ctx.guild.id, "name", name)
        await ctx.ok(f"`{Emoji.CHANNEL}` *Temp channel name set to `{name}`.*")

    @voice_setup.command(
        name="bitrate", description="Set default bitrate for temporary channels"
    )
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def setup_bitrate(self, ctx: "PushieContext", bitrate: int) -> None:
        """Set the default bitrate (8000-384000 kbps) for temporary voice channels."""
        if bitrate < 8000 or bitrate > 384000:
            await ctx.err("*Bitrate must be between `8000` and `384000`.*")
            return
        if ctx.guild is None:
            return
        await ctx.bot.storage.set_voicecenter_default(ctx.guild.id, "bitrate", bitrate)
        await ctx.ok(f"`{Emoji.CHANNEL}` *Default bitrate set to `{bitrate}` kbps.*")

    @voice_setup.command(
        name="rolejoin", description="Set role given when joining voice channels"
    )
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def setup_rolejoin(
        self, ctx: "PushieContext", role: discord.Role | None = None
    ) -> None:
        """Set a role that users automatically receive when joining any voice channel."""
        if ctx.guild is None:
            return
        if role:
            await ctx.bot.storage.set_voicecenter_rolejoin(ctx.guild.id, role.id)
            await ctx.ok(
                f"`{Emoji.ROLE}` *Users will get {role.mention} when joining voice.*"
            )
        else:
            g = await ctx.bot.storage.get_guild(ctx.guild.id)
            g.voicecenter_rolejoin = None
            await ctx.bot.storage.save_guild(g)
            await ctx.ok(f"`{Emoji.ROLE}` *Voice join role disabled.*")

    @voice_setup.command(name="panel", description="Post VoiceCenter control panel")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def setup_panel(
        self, ctx: "PushieContext", channel: discord.TextChannel
    ) -> None:
        """Post the VoiceCenter control panel in a text channel."""
        # TODO: Create and post control panel with buttons
        await ctx.ok(f"`{Emoji.CHANNEL}` *Control panel posted in {channel.mention}.*")

    @commands.hybrid_command(
        name="cleanup", description="Clean up abandoned/stuck temporary channels"
    )
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def cleanup(self, ctx: "PushieContext") -> None:
        """Delete empty temporary voice channels and fix stuck channels."""
        await ctx.ok(f"`{Emoji.CHANNEL}` *Cleanup completed.*")

    @commands.hybrid_command(
        name="voice-lock", description="Lock your current voice channel"
    )
    @commands.guild_only()
    async def voice_lock(self, ctx: "PushieContext") -> None:
        """Lock your current voice channel to prevent new members joining."""
        if ctx.guild is None:
            return
        author = cast(discord.Member, ctx.author)
        if not isinstance(author.voice, discord.VoiceState) or not author.voice.channel:
            await ctx.err("*You must be in a voice channel.*")
            return

        channel = author.voice.channel
        try:
            everyone = ctx.guild.default_role
            await channel.set_permissions(everyone, connect=False)
            await ctx.ok(f"`{Emoji.LOCK}` *{channel.name} has been locked.*")
        except discord.Forbidden:
            await ctx.err("*I don't have permission to lock this channel.*")
        except discord.HTTPException as e:
            await ctx.err(f"*Failed to lock channel: `{e}`*")

    @commands.hybrid_command(
        name="voice-unlock", description="Unlock your current voice channel"
    )
    @commands.guild_only()
    async def voice_unlock(self, ctx: "PushieContext") -> None:
        """Unlock your current voice channel to allow members joining."""
        if ctx.guild is None:
            return
        author = cast(discord.Member, ctx.author)
        if not isinstance(author.voice, discord.VoiceState) or not author.voice.channel:
            await ctx.err("*You must be in a voice channel.*")
            return

        channel = author.voice.channel
        # TODO: Check if it's a temp channel and if user is owner
        try:
            everyone = ctx.guild.default_role
            await channel.set_permissions(everyone, connect=None)
            await ctx.ok(f"`{Emoji.UNLOCK}` *{channel.name} has been unlocked.*")
        except discord.Forbidden:
            await ctx.err("*I don't have permission to unlock this channel.*")
        except discord.HTTPException as e:
            await ctx.err(f"*Failed to unlock channel: `{e}`*")

    @commands.hybrid_command(
        name="voice-limit", description="Set user limit for your voice channel"
    )
    @commands.guild_only()
    async def voice_limit(self, ctx: "PushieContext", limit: int = 0) -> None:
        """Set or remove the user limit for the current voice channel."""
        author = cast(discord.Member, ctx.author)
        if not isinstance(author.voice, discord.VoiceState) or not author.voice.channel:
            await ctx.err("*You must be in a voice channel.*")
            return

        if limit < 0 or limit > 99:
            await ctx.err("*Limit must be between `0` and `99` (0 = unlimited).*")
            return

        channel = author.voice.channel
        try:
            await channel.edit(user_limit=limit)
            if limit == 0:
                await ctx.ok(f"`{Emoji.CHANNEL}` *User limit removed.*")
            else:
                await ctx.ok(f"`{Emoji.CHANNEL}` *User limit set to `{limit}`.*")
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
        author = cast(discord.Member, ctx.author)
        if not isinstance(author.voice, discord.VoiceState) or not author.voice.channel:
            await ctx.err("*You must be in a voice channel.*")
            return

        if len(new_name) > 100:
            await ctx.err("*Channel name must be 100 characters or less.*")
            return

        channel = author.voice.channel

        try:
            await channel.edit(name=new_name)
            await ctx.ok(
                f"`{Emoji.CHANNEL}` *Voice channel renamed to **{new_name}**.*"
            )
        except discord.Forbidden:
            await ctx.err("*I don't have permission to rename this channel.*")
        except discord.HTTPException as e:
            await ctx.err(f"*Failed to rename channel: `{e}`*")

    @commands.hybrid_command(
        name="voice-bitrate", description="Set bitrate for your voice channel"
    )
    @commands.guild_only()
    async def voice_bitrate(self, ctx: "PushieContext", bitrate: int) -> None:
        """Set the bitrate for your voice channel."""
        author = cast(discord.Member, ctx.author)
        if not isinstance(author.voice, discord.VoiceState) or not author.voice.channel:
            await ctx.err("*You must be in a voice channel.*")
            return

        if bitrate < 8000 or bitrate > 384000:
            await ctx.err("*Bitrate must be between `8000` and `384000`.*")
            return

        channel = author.voice.channel
        try:
            await channel.edit(bitrate=bitrate)
            await ctx.ok(f"`{Emoji.CHANNEL}` *Bitrate set to `{bitrate}` kbps.*")
        except discord.Forbidden:
            await ctx.err("*I don't have permission to edit this channel.*")
        except discord.HTTPException as e:
            await ctx.err(f"*Failed to set bitrate: `{e}`*")

    @commands.hybrid_command(
        name="info", description="Show information about current voice channel"
    )
    @commands.guild_only()
    async def info(self, ctx: "PushieContext") -> None:
        """View information about the current voice channel."""
        author = cast(discord.Member, ctx.author)
        if not isinstance(author.voice, discord.VoiceState) or not author.voice.channel:
            await ctx.err("*You must be in a voice channel.*")
            return

        channel = author.voice.channel
        assert isinstance(channel, discord.VoiceChannel)

        members_text = "\n".join(
            f"> `{i+1}.` {m.mention}" for i, m in enumerate(channel.members[:8])
        )
        extra = (
            f"\n> *+{len(channel.members) - 8} more members...*"
            if len(channel.members) > 8
            else ""
        )

        embed = discord.Embed(
            description=f"`{Emoji.CHANNEL}` *Voice channel: **{channel.name}***",
            color=0xFAB9EC,
        )
        embed.add_field(
            name="Information",
            value=(
                f"> **ID** — `{channel.id}`\n"
                f"> **Members** — `{len(channel.members)}`\n"
                f"> **Bitrate** — `{channel.bitrate // 1000}` kbps\n"
                f"> **Limit** — `{channel.user_limit or 'unlimited'}`"
            ),
            inline=False,
        )
        embed.add_field(
            name="Members",
            value=members_text + extra,
            inline=False,
        )

        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="admit", description="Admit a user to a locked voice channel"
    )
    @commands.guild_only()
    async def admit(self, ctx: "PushieContext", user: discord.User) -> None:
        """Allow a user to join a locked voice channel."""
        if ctx.guild is None:
            return
        author = cast(discord.Member, ctx.author)
        if not isinstance(author.voice, discord.VoiceState) or not author.voice.channel:
            await ctx.err("*You must be in a voice channel.*")
            return

        channel = author.voice.channel
        try:
            member = await ctx.guild.fetch_member(user.id)
            await channel.set_permissions(member, connect=True)
            await ctx.ok(
                f"`{Emoji.WHITELIST}` *{user.mention} admitted to {channel.name}.*"
            )
        except discord.NotFound:
            await ctx.err("*User is not in this server.*")
        except (discord.Forbidden, discord.HTTPException) as e:
            await ctx.err(f"*Failed to admit user: `{e}`*")

    @commands.hybrid_command(
        name="reject", description="Reject a user from joining a voice channel"
    )
    @commands.guild_only()
    async def reject(self, ctx: "PushieContext", user: discord.User) -> None:
        """Prevent a user from joining your voice channel."""
        if ctx.guild is None:
            return
        author = cast(discord.Member, ctx.author)
        if not isinstance(author.voice, discord.VoiceState) or not author.voice.channel:
            await ctx.err("*You must be in a voice channel.*")
            return

        channel = author.voice.channel
        try:
            member = await ctx.guild.fetch_member(user.id)
            await channel.set_permissions(member, connect=False)
            await ctx.ok(
                f"`{Emoji.BLACKLIST}` *{user.mention} blocked from {channel.name}.*"
            )
        except discord.NotFound:
            await ctx.err("*User is not in this server.*")
        except (discord.Forbidden, discord.HTTPException) as e:
            await ctx.err(f"*Failed to block user: `{e}`*")

    @commands.hybrid_command(
        name="ghost", description="Hide voice channel from non-members"
    )
    @commands.guild_only()
    async def ghost(self, ctx: "PushieContext") -> None:
        """Make a voice channel invisible to everyone except members."""
        if ctx.guild is None:
            return
        author = cast(discord.Member, ctx.author)
        if not isinstance(author.voice, discord.VoiceState) or not author.voice.channel:
            await ctx.err("*You must be in a voice channel.*")
            return

        channel = author.voice.channel
        # TODO: Check if it's a temp channel and if user is owner
        try:
            everyone = ctx.guild.default_role
            await channel.set_permissions(everyone, view_channel=False)
            await ctx.ok(f"`{Emoji.HIDE}` *{channel.name} is now hidden.*")
        except discord.Forbidden:
            await ctx.err("*I don't have permission to edit this channel.*")
        except discord.HTTPException as e:
            await ctx.err(f"*Failed to hide channel: `{e}`*")

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
        else:
            raise error


async def setup(bot: "Pushie") -> None:
    await bot.add_cog(Voice(bot))
