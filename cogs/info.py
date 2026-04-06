from __future__ import annotations

import io
import logging
from typing import TYPE_CHECKING, Sequence

import discord
from discord.ext import commands
from PIL import Image, ImageEnhance, ImageDraw, ImageOps
import aiohttp

from emojis import Emoji
from ui import UI, BaseView

if TYPE_CHECKING:
    from main import Pushie, PushieContext

log = logging.getLogger(__name__)


def _format_permissions(permissions: discord.Permissions) -> str:
    perms = [p.replace("_", " ").title() for p, v in permissions if v]
    if not perms:
        return "*none*"
    return ", ".join(f"`{p}`" for p in perms[:10]) + (
        f" *+{len(perms) - 10} more*" if len(perms) > 10 else ""
    )


def _format_roles(roles: Sequence[discord.Role]) -> str:
    roles = [r for r in roles if r.name != "@everyone"]
    if not roles:
        return "*none*"
    roles = sorted(roles, reverse=True)
    preview = " ".join(r.mention for r in roles[:8])
    extra = f" *+{len(roles) - 8} more*" if len(roles) > 8 else ""
    return preview + extra


async def _fetch_bytes(session: aiohttp.ClientSession, url: str) -> bytes:
    async with session.get(url) as resp:
        resp.raise_for_status()
        return await resp.read()


async def _process_image(
    session: aiohttp.ClientSession,
    url: str,
    mode: str,  # "darken" | "lighten" | "round"
    factor: float = 0.5,
) -> discord.File:
    data = await _fetch_bytes(session, url)
    img = Image.open(io.BytesIO(data)).convert("RGBA")

    if mode == "darken":
        enhancer = ImageEnhance.Brightness(img.convert("RGB"))
        img = enhancer.enhance(max(0.0, 1.0 - factor)).convert("RGBA")
    elif mode == "lighten":
        enhancer = ImageEnhance.Brightness(img.convert("RGB"))
        img = enhancer.enhance(min(2.0, 1.0 + factor)).convert("RGBA")
    elif mode == "round":
        mask = Image.new("L", img.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, img.size[0], img.size[1]), fill=255)
        img.putalpha(mask)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return discord.File(buf, filename="image.png")


class DownloadView(BaseView):
    """Single button that links directly to the full-size asset."""

    def __init__(
        self,
        user: discord.User | discord.Member,
        url: str,
        label: str = "↓ Download",
    ) -> None:
        super().__init__(user, timeout=120)
        self.add_item(
            discord.ui.Button(
                label=label,
                style=discord.ButtonStyle.link,
                url=url,
            )
        )


class _AssetLinkModal(discord.ui.Modal):
    link = discord.ui.TextInput(
        label="Image URL",
        placeholder="https://...",
        max_length=500,
    )

    def __init__(self, title: str) -> None:
        super().__init__(title=title)
        self.value: str | None = None

    async def on_submit(self, interaction: discord.Interaction) -> None:
        self.value = self.link.value.strip()
        await interaction.response.defer()
        self.stop()

    async def on_error(
        self, interaction: discord.Interaction, error: Exception
    ) -> None:
        await interaction.response.send_message(
            embed=UI.error("Invalid input."), ephemeral=True
        )
        self.stop()


class Info(commands.Cog, name="Info"):
    """Server, user, channel and image info commands."""

    def __init__(self, bot: "Pushie") -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="serverinfo", aliases=["si"], description="Show server information"
    )
    @commands.guild_only()
    async def serverinfo(self, ctx: "PushieContext") -> None:
        g = ctx.guild
        assert g is not None

        created = discord.utils.format_dt(g.created_at, style="D")
        created_rel = discord.utils.format_dt(g.created_at, style="R")

        total = g.member_count or 0
        bots = sum(1 for m in g.members if m.bot)
        humans = total - bots
        text_ch = len(g.text_channels)
        voice_ch = len(g.voice_channels)
        categories = len(g.categories)

        embed = discord.Embed(
            description=(
                f"> `{Emoji.INFO}` *{g.description or 'No description set.'}*"
            ),
            color=0xFAB9EC,
        )
        embed.set_author(name=g.name, icon_url=g.icon.url if g.icon else None)
        if g.banner:
            embed.set_image(url=g.banner.url)
        if g.icon:
            embed.set_thumbnail(url=g.icon.url)

        embed.add_field(
            name=f"`{Emoji.INFO}` General",
            value=(
                f"> **Owner** — {g.owner.mention if g.owner else '*unknown*'}\n"
                f"> **Created** — {created} ({created_rel})\n"
                f"> **ID** — `{g.id}`\n"
                f"> **Verification** — `{g.verification_level}`\n"
                f"> **Locale** — `{g.preferred_locale}`"
            ),
            inline=False,
        )
        embed.add_field(
            name=f"`{Emoji.STATS}` Members",
            value=(
                f"> **Total** — `{total}`\n"
                f"> **Humans** — `{humans}`\n"
                f"> **Bots** — `{bots}`"
            ),
            inline=True,
        )
        embed.add_field(
            name=f"`{Emoji.CHANNEL}` Channels",
            value=(
                f"> **Text** — `{text_ch}`\n"
                f"> **Voice** — `{voice_ch}`\n"
                f"> **Categories** — `{categories}`"
            ),
            inline=True,
        )
        embed.add_field(
            name=f"`{Emoji.BOOSTER}` Boosts",
            value=(
                f"> **Level** — `{g.premium_tier}`\n"
                f"> **Count** — `{g.premium_subscription_count or 0}`"
            ),
            inline=True,
        )
        embed.add_field(
            name=f"`{Emoji.ROLE}` Roles `{len(g.roles)}`",
            value=_format_roles(g.roles),
            inline=False,
        )
        embed.set_footer(
            text=(
                f"Shard #{g.shard_id}"
                if g.shard_id is not None
                else discord.utils.MISSING
            )
        )

        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="channelinfo", aliases=["ci"], description="Show channel information"
    )
    @commands.guild_only()
    async def channelinfo(
        self,
        ctx: "PushieContext",
        *,
        channel: discord.abc.GuildChannel | None = None,
    ) -> None:
        ch = channel or ctx.channel
        assert ch is not None and isinstance(ch, discord.abc.GuildChannel)

        created = (
            discord.utils.format_dt(ch.created_at, style="D")
            if ch.created_at
            else "*unknown*"
        )
        created_rel = (
            discord.utils.format_dt(ch.created_at, style="R") if ch.created_at else ""
        )

        lines = [
            f"> **Name** — `{ch.name}`",
            f"> **ID** — `{ch.id}`",
            f"> **Type** — `{str(ch.type).replace('_', ' ').title()}`",
            f"> **Created** — {created} {created_rel}",
        ]

        if isinstance(ch, discord.TextChannel):
            lines += [
                f"> **Category** — `{ch.category or 'none'}`",
                f"> **Topic** — *{ch.topic or 'none'}*",
                f"> **Slowmode** — `{ch.slowmode_delay}s`",
                f"> **NSFW** — `{ch.is_nsfw()}`",
            ]
        elif isinstance(ch, discord.VoiceChannel):
            lines += [
                f"> **Bitrate** — `{ch.bitrate // 1000}kbps`",
                f"> **User limit** — `{ch.user_limit or 'unlimited'}`",
            ]
        elif isinstance(ch, discord.CategoryChannel):
            lines.append(f"> **Channels** — `{len(ch.channels)}`")

        embed = discord.Embed(
            description=f"> `{Emoji.CHANNEL}` *Channel info for {ch.mention}*\n\n"
            + "\n".join(lines),
            color=0xFAB9EC,
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="userinfo", aliases=["ui"], description="Show user information"
    )
    @commands.guild_only()
    async def userinfo(
        self,
        ctx: "PushieContext",
        *,
        member: discord.Member | None = None,
    ) -> None:
        m = member or ctx.author
        assert isinstance(m, discord.Member)

        joined = (
            discord.utils.format_dt(m.joined_at, style="D")
            if m.joined_at
            else "*unknown*"
        )
        joined_rel = (
            discord.utils.format_dt(m.joined_at, style="R") if m.joined_at else ""
        )
        created = discord.utils.format_dt(m.created_at, style="D")
        created_rel = discord.utils.format_dt(m.created_at, style="R")

        badges: list[str] = []
        if m.bot:
            badges.append("`BOT`")
        if m.premium_since:
            badges.append(f"`{Emoji.BOOSTER} BOOSTER`")
        if ctx.guild and m.id == ctx.guild.owner_id:
            badges.append(f"`{Emoji.ROLE} OWNER`")

        embed = discord.Embed(
            description=(
                f"> `{Emoji.INFO}` *{' · '.join(badges) if badges else 'Member'}*"
            ),
            color=m.color if m.color.value else 0xFAB9EC,
        )
        embed.set_author(name=str(m), icon_url=m.display_avatar.url)
        embed.set_thumbnail(url=m.display_avatar.url)

        embed.add_field(
            name=f"`{Emoji.INFO}` General",
            value=(
                f"> **Mention** — {m.mention}\n"
                f"> **ID** — `{m.id}`\n"
                f"> **Nick** — `{m.nick or 'none'}`\n"
                f"> **Created** — {created} ({created_rel})\n"
                f"> **Joined** — {joined} {joined_rel}"
            ),
            inline=False,
        )
        embed.add_field(
            name=f"`{Emoji.ROLE}` Roles `{len(m.roles) - 1}`",
            value=_format_roles(m.roles),
            inline=False,
        )
        embed.add_field(
            name=f"`{Emoji.LOCK}` Key Permissions",
            value=_format_permissions(m.guild_permissions),
            inline=False,
        )

        view = DownloadView(ctx.author, m.display_avatar.url, "↓ Avatar")
        await ctx.send(embed=embed, view=view)

    @commands.hybrid_command(
        name="botinfo", aliases=["bi"], description="Show bot information"
    )
    async def botinfo(self, ctx: "PushieContext") -> None:
        bot = self.bot
        assert bot.user is not None

        up = str(bot.uptime).split(".")[0]
        guilds = len(bot.guilds)
        users = sum(g.member_count or 0 for g in bot.guilds)
        created = discord.utils.format_dt(bot.user.created_at, style="D")
        created_rel = discord.utils.format_dt(bot.user.created_at, style="R")

        embed = discord.Embed(
            description=f"> `{Emoji.PUSHEEN}` *Pushie Pusheen — a cozy multipurpose bot* 🐱",
            color=0xFAB9EC,
        )
        embed.set_author(name=str(bot.user), icon_url=bot.user.display_avatar.url)
        embed.set_thumbnail(url=bot.user.display_avatar.url)

        embed.add_field(
            name=f"`{Emoji.STATS}` Stats",
            value=(
                f"> **Guilds** — `{guilds}`\n"
                f"> **Users** — `{users}`\n"
                f"> **Uptime** — `{up}`\n"
                f"> **Latency** — `{round(bot.latency * 1000)}ms`"
            ),
            inline=True,
        )
        embed.add_field(
            name=f"`{Emoji.INFO}` Info",
            value=(
                f"> **ID** — `{bot.user.id}`\n"
                f"> **Created** — {created} ({created_rel})\n"
                f"> **Prefix** — `!` *(or mention)*\n"
                f"> **Commands** — `{len(bot.commands)}`"
            ),
            inline=True,
        )

        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="banner", aliases=["bn"], description="Show a user's banner"
    )
    async def banner(
        self,
        ctx: "PushieContext",
        *,
        user: discord.User | None = None,
    ) -> None:
        target = user or ctx.author
        fetched = await self.bot.fetch_user(target.id)

        if not fetched.banner:
            await ctx.send(
                embed=UI.error(f"*{fetched.display_name} has no banner set.*")
            )
            return

        url = fetched.banner.url
        embed = discord.Embed(
            description=f"> `{Emoji.IMAGE}` *Banner for **{fetched.display_name}***",
            color=0xFAB9EC,
        )
        embed.set_image(url=url)
        embed.set_footer(text=f"ID: {fetched.id}")

        view = DownloadView(
            ctx.author, fetched.banner.with_size(4096).url, "↓ Download"
        )
        await ctx.send(embed=embed, view=view)

    @commands.hybrid_command(
        name="avatar", aliases=["av"], description="Show a user's avatar"
    )
    async def avatar(
        self,
        ctx: "PushieContext",
        *,
        user: discord.User | None = None,
    ) -> None:
        target = user or ctx.author
        av = target.display_avatar.with_size(4096)

        embed = discord.Embed(
            description=f"> `{Emoji.IMAGE}` *Avatar for **{target.display_name}***",
            color=0xFAB9EC,
        )
        embed.set_image(url=av.url)
        embed.set_footer(text=f"ID: {target.id}")

        view = DownloadView(ctx.author, av.url, "↓ Download")
        await ctx.send(embed=embed, view=view)

    @commands.hybrid_command(
        name="sbanner",
        aliases=["sbn"],
        description="Show your server-specific banner (Nitro only)",
    )
    @commands.guild_only()
    async def sbanner(
        self,
        ctx: "PushieContext",
        *,
        member: discord.Member | None = None,
    ) -> None:
        m = member or ctx.author
        assert isinstance(m, discord.Member)

        if not m.banner:
            await ctx.send(
                embed=UI.error(
                    f"*{m.display_name} has no server banner — this requires Nitro.*"
                )
            )
            return

        url = m.banner.with_size(4096).url
        embed = discord.Embed(
            description=f"> `{Emoji.IMAGE}` *Server banner for **{m.display_name}***",
            color=0xFAB9EC,
        )
        embed.set_image(url=url)
        embed.set_footer(text=f"ID: {m.id}")

        view = DownloadView(ctx.author, url, "↓ Download")
        await ctx.send(embed=embed, view=view)

    @commands.hybrid_command(
        name="sav", description="Show your server-specific avatar (Nitro only)"
    )
    @commands.guild_only()
    async def sav(
        self,
        ctx: "PushieContext",
        *,
        member: discord.Member | None = None,
    ) -> None:
        m = member or ctx.author
        assert isinstance(m, discord.Member)

        if not m.guild_avatar:
            await ctx.send(
                embed=UI.error(
                    f"*{m.display_name} has no server avatar — this requires Nitro.*"
                )
            )
            return

        url = m.guild_avatar.with_size(4096).url
        embed = discord.Embed(
            description=f"> `{Emoji.IMAGE}` *Server avatar for **{m.display_name}***",
            color=0xFAB9EC,
        )
        embed.set_image(url=url)
        embed.set_footer(text=f"ID: {m.id}")

        view = DownloadView(ctx.author, url, "↓ Download")
        await ctx.send(embed=embed, view=view)

    @commands.group(
        name="icon",
        aliases=["ic"],
        invoke_without_command=True,
    )
    @commands.guild_only()
    async def icon(self, ctx: "PushieContext") -> None:
        """View the server icon. Use `!icon set` to change it."""
        g = ctx.guild
        assert g is not None

        if not g.icon:
            await ctx.send(embed=UI.error("*This server has no icon.*"))
            return

        url = g.icon.with_size(4096).url
        embed = discord.Embed(
            description=f"> `{Emoji.IMAGE}` *Server icon for **{g.name}***",
            color=0xFAB9EC,
        )
        embed.set_image(url=url)

        view = DownloadView(ctx.author, url, "↓ Download")
        await ctx.send(embed=embed, view=view)

    @icon.command(name="set")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def icon_set(self, ctx: "PushieContext", *, link: str | None = None) -> None:
        """Set the server icon. Attach an image or pass a URL."""
        g = ctx.guild
        assert g is not None

        image_bytes: bytes | None = None

        if ctx.message.attachments:
            image_bytes = await ctx.message.attachments[0].read()
        elif link:
            try:
                image_bytes = await _fetch_bytes(self.bot.session, link)
            except Exception:
                await ctx.send(embed=UI.error("*Could not fetch image from that URL.*"))
                return
        else:
            await ctx.send(embed=UI.error("*Attach an image or provide a URL: `!icon set <url>`*"))
            return

        try:
            await g.edit(icon=image_bytes)
            await ctx.send(embed=UI.success("*Server icon updated!*"))
        except discord.Forbidden:
            await ctx.send(embed=UI.error("*I don't have permission to change the server icon.*"))
        except discord.HTTPException as e:
            await ctx.send(embed=UI.error(f"*Failed to update icon: `{e}`*"))

    @commands.group(
        name="gbanner",
        aliases=["gbn"],
        invoke_without_command=True,
    )
    @commands.guild_only()
    async def gbanner(self, ctx: "PushieContext") -> None:
        """View the server banner. Use `!gbanner set` to change it."""
        g = ctx.guild
        assert g is not None

        if not g.banner:
            await ctx.send(
                embed=UI.error("*This server has no banner — requires boost level 2.*")
            )
            return

        url = g.banner.with_size(4096).url
        embed = discord.Embed(
            description=f"> `{Emoji.IMAGE}` *Server banner for **{g.name}***",
            color=0xFAB9EC,
        )
        embed.set_image(url=url)
        embed.set_footer(text=f"Boost level {g.premium_tier}")

        view = DownloadView(ctx.author, url, "↓ Download")
        await ctx.send(embed=embed, view=view)

    @gbanner.command(name="set")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def gbanner_set(
        self, ctx: "PushieContext", *, link: str | None = None
    ) -> None:
        """Set the server banner. Attach an image or pass a URL."""
        g = ctx.guild
        assert g is not None

        if g.premium_tier < 2:
            await ctx.send(
                embed=UI.error("*Setting a server banner requires **boost level 2**.*")
            )
            return

        image_bytes: bytes | None = None

        if ctx.message.attachments:
            image_bytes = await ctx.message.attachments[0].read()
        elif link:
            try:
                image_bytes = await _fetch_bytes(self.bot.session, link)
            except Exception:
                await ctx.send(embed=UI.error("*Could not fetch image from that URL.*"))
                return
        else:
            await ctx.send(embed=UI.error("*Attach an image or provide a URL: `!gbanner set <url>`*"))
            return

        try:
            await g.edit(banner=image_bytes)
            await ctx.send(embed=UI.success("*Server banner updated!*"))
        except discord.Forbidden:
            await ctx.send(embed=UI.error("*I don't have permission to change the server banner.*"))
        except discord.HTTPException as e:
            await ctx.send(embed=UI.error(f"*Failed to update banner: `{e}`*"))

    @commands.group(
        name="image",
        aliases=["img"],
        invoke_without_command=True,
    )
    async def image(self, ctx: "PushieContext") -> None:
        """Image tools (prefix-only — attach an image): darken, lighten, round."""
        await ctx.send(
            embed=UI.info(
                f"*Image tools:*\n"
                f"```\n"
                f"{ctx.prefix}image darken [factor] — darken an image\n"
                f"{ctx.prefix}image lighten [factor] — lighten an image\n"
                f"{ctx.prefix}image round — round-crop an image\n"
                f"```\n"
                f"*Attach an image or reply to one.*"
            )
        )

    async def _get_image_url(self, ctx: "PushieContext") -> str | None:
        if ctx.message.attachments:
            return ctx.message.attachments[0].url
        if ctx.message.reference:
            ref = ctx.message.reference.resolved
            if isinstance(ref, discord.Message) and ref.attachments:
                return ref.attachments[0].url
        await ctx.send(
            embed=UI.error("*Attach an image or reply to a message with one.*")
        )
        return None

    @image.command(name="darken")
    async def image_darken(
        self,
        ctx: "PushieContext",
        factor: float = 0.4,
    ) -> None:
        """Darken an attached image (factor 0.0–1.0, default 0.4)."""
        url = await self._get_image_url(ctx)
        if not url:
            return
        if not (0.0 < factor <= 1.0):
            await ctx.send(embed=UI.error("*Factor must be between `0.0` and `1.0`.*"))
            return
        async with ctx.typing():
            file = await _process_image(self.bot.session, url, "darken", factor)
        embed = discord.Embed(
            description=f"> `{Emoji.IMAGE}` *Darkened by `{factor}`*",
            color=0xFAB9EC,
        )
        embed.set_image(url="attachment://image.png")
        await ctx.send(embed=embed, file=file)

    @image.command(name="lighten")
    async def image_lighten(
        self,
        ctx: "PushieContext",
        factor: float = 0.4,
    ) -> None:
        """Lighten an attached image (factor 0.0–1.0, default 0.4)."""
        url = await self._get_image_url(ctx)
        if not url:
            return
        if not (0.0 < factor <= 1.0):
            await ctx.send(embed=UI.error("*Factor must be between `0.0` and `1.0`.*"))
            return
        async with ctx.typing():
            file = await _process_image(self.bot.session, url, "lighten", factor)
        embed = discord.Embed(
            description=f"> `{Emoji.IMAGE}` *Lightened by `{factor}`*",
            color=0xFAB9EC,
        )
        embed.set_image(url="attachment://image.png")
        await ctx.send(embed=embed, file=file)

    @image.command(name="round")
    async def image_round(self, ctx: "PushieContext") -> None:
        """Round-crop an attached image."""
        url = await self._get_image_url(ctx)
        if not url:
            return
        async with ctx.typing():
            file = await _process_image(self.bot.session, url, "round")
        embed = discord.Embed(
            description=f"> `{Emoji.IMAGE}` *Round cropped*",
            color=0xFAB9EC,
        )
        embed.set_image(url="attachment://image.png")
        await ctx.send(embed=embed, file=file)

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
            await ctx.send(
                embed=UI.error("*This command can only be used in a server.*")
            )
        else:
            raise error


async def setup(bot: "Pushie") -> None:
    await bot.add_cog(Info(bot))
