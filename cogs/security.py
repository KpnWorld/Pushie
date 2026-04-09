from __future__ import annotations

import logging
import re
import time
from typing import TYPE_CHECKING

import discord
from discord.ext import commands

from emojis import Emoji
from ui import UI

if TYPE_CHECKING:
    from main import Pushie, PushieContext

log = logging.getLogger(__name__)


class Security(commands.Cog, name="Security"):
    """Message filtering, antinuke, fake permissions, and antiraid protection."""

    def __init__(self, bot: "Pushie") -> None:
        self.bot = bot
        # In-memory antiraid join tracker: guild_id -> [timestamp, ...]
        self._join_times: dict[int, list[float]] = {}

    # ======== Filter Enforcement ========

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot or not message.guild:
            return
        g = self.bot.storage.get_guild_sync(message.guild.id)
        if not g:
            return
        author_id = message.author.id
        # Exemptions
        if author_id in g.filter_exempts:
            return
        if self.bot.storage.is_sudo(author_id):
            return
        if isinstance(message.author, discord.Member):
            if message.author.guild_permissions.manage_messages:
                return

        content_lower = message.content.lower()

        # Keyword filter
        for kw in g.keyword_filters:
            if kw.lower() in content_lower:
                try:
                    await message.delete()
                    await message.channel.send(  # type: ignore
                        embed=UI.error(f"*{message.author.mention} — message removed (keyword filter).*"),
                        delete_after=4,
                    )
                except (discord.Forbidden, discord.HTTPException):
                    pass
                return

        # Regex filter
        for pattern in g.regex_filters:
            try:
                if re.search(pattern, message.content, re.IGNORECASE):
                    try:
                        await message.delete()
                        await message.channel.send(  # type: ignore
                            embed=UI.error(f"*{message.author.mention} — message removed (regex filter).*"),
                            delete_after=4,
                        )
                    except (discord.Forbidden, discord.HTTPException):
                        pass
                    return
            except re.error:
                pass

        # Invite filter
        if g.invite_filters:
            invite_re = re.compile(r"discord\.gg/|discord\.com/invite/")
            if invite_re.search(message.content):
                try:
                    await message.delete()
                    await message.channel.send(  # type: ignore
                        embed=UI.error(f"*{message.author.mention} — Discord invites are not allowed here.*"),
                        delete_after=4,
                    )
                except (discord.Forbidden, discord.HTTPException):
                    pass
                return

        # Link filter
        if g.link_filters:
            link_re = re.compile(r"https?://\S+")
            links_found = link_re.findall(message.content)
            for link in links_found:
                domain = link.split("/")[2] if len(link.split("/")) > 2 else ""
                # Check against whitelist
                whitelisted = any(w in link for w in g.filter_link_whitelist)
                if whitelisted:
                    continue
                # Check if domain matches filter
                if any(f in domain for f in g.link_filters):
                    try:
                        await message.delete()
                        await message.channel.send(  # type: ignore
                            embed=UI.error(f"*{message.author.mention} — that link is not allowed here.*"),
                            delete_after=4,
                        )
                    except (discord.Forbidden, discord.HTTPException):
                        pass
                    return

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        guild = member.guild
        g = self.bot.storage.get_guild_sync(guild.id)
        if not g:
            return

        if g.antiraid_enabled:
            # Antiraid - username patterns
            for pattern in g.antiraid_username_patterns:
                try:
                    if re.search(pattern, member.name, re.IGNORECASE):
                        if member.id not in g.antiraid_whitelist:
                            try:
                                await member.kick(reason="Antiraid: username pattern match")
                            except (discord.Forbidden, discord.HTTPException):
                                pass
                            return
                except re.error:
                    pass

            # Antiraid - default avatar
            if g.antiraid_avatar and not member.avatar:
                if member.id not in g.antiraid_whitelist:
                    try:
                        await member.kick(reason="Antiraid: default avatar")
                    except (discord.Forbidden, discord.HTTPException):
                        pass
                    return

            # Antiraid - account age (< 7 days)
            if g.antiraid_age:
                age_days = (discord.utils.utcnow() - member.created_at).days
                if age_days < 7 and member.id not in g.antiraid_whitelist:
                    try:
                        await member.kick(reason="Antiraid: new account")
                    except (discord.Forbidden, discord.HTTPException):
                        pass
                    return

            # Antiraid - unverified bots
            if g.antiraid_unverifiedbots and member.bot:
                if member.id not in g.antiraid_whitelist:
                    try:
                        await member.kick(reason="Antiraid: unverified bot")
                    except (discord.Forbidden, discord.HTTPException):
                        pass
                    return

            # Antiraid - mass join detection
            if g.antiraid_massjoin:
                now = time.time()
                joins = self._join_times.setdefault(guild.id, [])
                joins.append(now)
                # Clean old entries (> 10 seconds)
                self._join_times[guild.id] = [t for t in joins if now - t < 10]
                if len(self._join_times[guild.id]) >= 5:
                    if member.id not in g.antiraid_whitelist:
                        try:
                            await member.kick(reason="Antiraid: mass join")
                        except (discord.Forbidden, discord.HTTPException):
                            pass
                        return

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member) -> None:
        guild = after.guild
        g = self.bot.storage.get_guild_sync(guild.id)
        if not g or not g.antinuke_enabled:
            return

        # Nickname filter
        if after.nick and before.nick != after.nick:
            for nf in g.nickname_filters:
                if nf.lower() in after.nick.lower():
                    try:
                        await after.edit(nick=before.nick, reason="Antinuke: nickname filter")
                    except (discord.Forbidden, discord.HTTPException):
                        pass
                    break

    # ======== Filter Commands ========

    @commands.group(name="filter", aliases=["fil"], invoke_without_command=True)
    @commands.guild_only()
    @commands.has_guild_permissions(administrator=True)
    async def filter(self, ctx: "PushieContext") -> None:
        """Automod filter management."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        kw = len(g.keyword_filters)
        lk = len(g.link_filters)
        rg = len(g.regex_filters)
        inv = "enabled" if g.invite_filters else "disabled"
        prefix = ctx.prefix or "!"
        await ctx.send(
            embed=UI.info(
                f"`{Emoji.BLACKLIST}` **Filter System**\n\n"
                f"> **Keywords:** `{kw}` | **Links:** `{lk}` | **Regex:** `{rg}`\n"
                f"> **Invites:** `{inv}`\n\n"
                f"```\n{prefix}filter list\n"
                f"{prefix}filter keyword add <word>\n"
                f"{prefix}filter keyword remove <word>\n"
                f"{prefix}filter link add <domain>\n"
                f"{prefix}filter link remove <domain>\n"
                f"{prefix}filter invites add\n"
                f"{prefix}filter invites remove\n"
                f"{prefix}filter regex add <pattern>\n"
                f"{prefix}filter regex test <text>\n"
                f"{prefix}filter whitelist <word>\n"
                f"{prefix}filter links whitelist <domain>\n"
                f"{prefix}filter nicknames <name>\n"
                f"{prefix}filter exempt <user>\n"
                f"{prefix}filter snipe\n```"
            )
        )

    @filter.command(name="list")
    async def filter_list(self, ctx: "PushieContext") -> None:
        """List all active filters."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        lines = []
        if g.keyword_filters:
            kws = ", ".join(f"`{k}`" for k in g.keyword_filters[:20])
            lines.append(f"> **Keywords:** {kws}")
        if g.link_filters:
            lks = ", ".join(f"`{l}`" for l in g.link_filters[:20])
            lines.append(f"> **Links:** {lks}")
        if g.regex_filters:
            rgs = ", ".join(f"`{r}`" for r in g.regex_filters[:10])
            lines.append(f"> **Regex:** {rgs}")
        if g.invite_filters:
            lines.append("> **Invites:** enabled")
        if g.nickname_filters:
            nks = ", ".join(f"`{n}`" for n in g.nickname_filters[:10])
            lines.append(f"> **Nicknames:** {nks}")
        if g.filter_exempts:
            exs = ", ".join(f"<@{e}>" for e in g.filter_exempts[:10])
            lines.append(f"> **Exempts:** {exs}")
        if not lines:
            await ctx.info("*No filters configured.*")
            return
        await ctx.send(embed=UI.info(f"`{Emoji.BLACKLIST}` **Active Filters**\n\n" + "\n".join(lines)))

    @filter.group(name="keyword", invoke_without_command=True)
    async def filter_keyword(self, ctx: "PushieContext") -> None:
        """Keyword filter management."""
        prefix = ctx.prefix or "!"
        await ctx.info(f"Usage: `{prefix}filter keyword add <word>` or `{prefix}filter keyword remove <word>`")

    @filter_keyword.command(name="add")
    async def filter_keyword_add(self, ctx: "PushieContext", *, word: str) -> None:
        """Add keyword to filter."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        word_lower = word.lower()
        if word_lower not in g.keyword_filters:
            g.keyword_filters.append(word_lower)
            await self.bot.storage.save_guild(g)
        await ctx.ok(f"*Added keyword filter: `{word_lower}`*")

    @filter_keyword.command(name="remove")
    async def filter_keyword_remove(self, ctx: "PushieContext", *, word: str) -> None:
        """Remove keyword from filter."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        word_lower = word.lower()
        if word_lower in g.keyword_filters:
            g.keyword_filters.remove(word_lower)
            await self.bot.storage.save_guild(g)
            await ctx.ok(f"*Removed keyword filter: `{word_lower}`*")
        else:
            await ctx.err(f"*`{word_lower}` is not in the keyword filter.*")

    @filter.group(name="link", invoke_without_command=True)
    async def filter_link(self, ctx: "PushieContext") -> None:
        """Link filter management."""
        prefix = ctx.prefix or "!"
        await ctx.info(f"Usage: `{prefix}filter link add <domain>` or `{prefix}filter link remove <domain>`")

    @filter_link.command(name="add")
    async def filter_link_add(self, ctx: "PushieContext", *, domain: str) -> None:
        """Add domain to link filter."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        if domain not in g.link_filters:
            g.link_filters.append(domain)
            await self.bot.storage.save_guild(g)
        await ctx.ok(f"*Added link filter: `{domain}`*")

    @filter_link.command(name="remove")
    async def filter_link_remove(self, ctx: "PushieContext", *, domain: str) -> None:
        """Remove domain from link filter."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        if domain in g.link_filters:
            g.link_filters.remove(domain)
            await self.bot.storage.save_guild(g)
            await ctx.ok(f"*Removed link filter: `{domain}`*")
        else:
            await ctx.err(f"*`{domain}` not in link filter.*")

    @filter.group(name="invites", invoke_without_command=True)
    async def filter_invites(self, ctx: "PushieContext") -> None:
        """Discord invite link filter."""
        prefix = ctx.prefix or "!"
        await ctx.info(f"Usage: `{prefix}filter invites add` or `{prefix}filter invites remove`")

    @filter_invites.command(name="add")
    async def filter_invites_add(self, ctx: "PushieContext") -> None:
        """Enable invite filter."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        if "all" not in g.invite_filters:
            g.invite_filters.append("all")
            await self.bot.storage.save_guild(g)
        await ctx.ok("*Discord invite filter enabled.*")

    @filter_invites.command(name="remove")
    async def filter_invites_remove(self, ctx: "PushieContext") -> None:
        """Disable invite filter."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        g.invite_filters.clear()
        await self.bot.storage.save_guild(g)
        await ctx.ok("*Discord invite filter disabled.*")

    @filter.group(name="regex", invoke_without_command=True)
    async def filter_regex(self, ctx: "PushieContext") -> None:
        """Regex filter management."""
        prefix = ctx.prefix or "!"
        await ctx.info(f"Usage: `{prefix}filter regex add <pattern>` or `{prefix}filter regex test <text>`")

    @filter_regex.command(name="add")
    async def filter_regex_add(self, ctx: "PushieContext", *, pattern: str) -> None:
        """Add regex pattern to filter."""
        assert ctx.guild is not None
        try:
            re.compile(pattern)
        except re.error as e:
            await ctx.err(f"*Invalid regex: `{e}`*")
            return
        g = await self.bot.storage.get_guild(ctx.guild.id)
        if pattern not in g.regex_filters:
            g.regex_filters.append(pattern)
            await self.bot.storage.save_guild(g)
        await ctx.ok(f"*Added regex filter: `{pattern}`*")

    @filter_regex.command(name="test")
    async def filter_regex_test(self, ctx: "PushieContext", *, text: str) -> None:
        """Test regex filters against text."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        matched = []
        for pattern in g.regex_filters:
            try:
                if re.search(pattern, text, re.IGNORECASE):
                    matched.append(f"`{pattern}`")
            except re.error:
                pass
        if matched:
            await ctx.send(embed=UI.warning(f"*Text matched: {', '.join(matched)}*"))
        else:
            await ctx.ok("*No regex filters matched.*")

    @filter.command(name="whitelist")
    async def filter_whitelist(self, ctx: "PushieContext", *, word: str) -> None:
        """Add word to keyword whitelist."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        if word not in g.filter_whitelist:
            g.filter_whitelist.append(word)
            await self.bot.storage.save_guild(g)
        await ctx.ok(f"*Added `{word}` to whitelist.*")

    @filter.command(name="links")
    async def filter_links_whitelist(self, ctx: "PushieContext", *, domain: str) -> None:
        """Add domain to link whitelist."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        if domain not in g.filter_link_whitelist:
            g.filter_link_whitelist.append(domain)
            await self.bot.storage.save_guild(g)
        await ctx.ok(f"*Added `{domain}` to link whitelist.*")

    @filter.command(name="snipe")
    async def filter_snipe(self, ctx: "PushieContext") -> None:
        """Toggle snipe filtering (deleted messages from snipe)."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        g.filter_snipe = not g.filter_snipe
        await self.bot.storage.save_guild(g)
        state = "enabled" if g.filter_snipe else "disabled"
        await ctx.ok(f"*Snipe filter {state}.*")

    @filter.command(name="nicknames")
    async def filter_nicknames(self, ctx: "PushieContext", *, name: str) -> None:
        """Add nickname pattern to filter."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        if name not in g.nickname_filters:
            g.nickname_filters.append(name)
            await self.bot.storage.save_guild(g)
        await ctx.ok(f"*Added nickname filter: `{name}`*")

    @filter.command(name="exempt")
    async def filter_exempt(self, ctx: "PushieContext", member: discord.Member) -> None:
        """Exempt a user from all filters."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        if member.id in g.filter_exempts:
            g.filter_exempts.remove(member.id)
            await self.bot.storage.save_guild(g)
            await ctx.ok(f"*{member.mention} removed from filter exemptions.*")
        else:
            g.filter_exempts.append(member.id)
            await self.bot.storage.save_guild(g)
            await ctx.ok(f"*{member.mention} added to filter exemptions.*")

    @filter.command(name="add")
    async def filter_add(self, ctx: "PushieContext", *, word: str) -> None:
        """Add general keyword filter."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        w = word.lower()
        if w not in g.keyword_filters:
            g.keyword_filters.append(w)
            await self.bot.storage.save_guild(g)
        await ctx.ok(f"*Filter added: `{w}`*")

    @filter.command(name="remove")
    async def filter_remove(self, ctx: "PushieContext", *, word: str) -> None:
        """Remove general keyword filter."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        w = word.lower()
        if w in g.keyword_filters:
            g.keyword_filters.remove(w)
            await self.bot.storage.save_guild(g)
            await ctx.ok(f"*Filter removed: `{w}`*")
        else:
            await ctx.err(f"*`{w}` not in filter.*")

    # ======== Antinuke ========

    @commands.group(name="antinuke", invoke_without_command=True)
    @commands.guild_only()
    @commands.has_guild_permissions(administrator=True)
    async def antinuke(self, ctx: "PushieContext") -> None:
        """Antinuke configuration."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        enabled = f"`{Emoji.SUCCESS}` enabled" if g.antinuke_enabled else f"`{Emoji.CANCEL}` disabled"
        prefix = ctx.prefix or "!"
        await ctx.send(
            embed=UI.info(
                f"`{Emoji.LOCK}` **Antinuke** — {enabled}\n\n"
                f"> **Kick protection:** `{'on' if g.antinuke_kick else 'off'}`\n"
                f"> **Ban protection:** `{'on' if g.antinuke_ban else 'off'}`\n"
                f"> **Vanity protection:** `{'on' if g.antinuke_vanity else 'off'}`\n"
                f"> **Guild update protection:** `{'on' if g.antinuke_guildupdate else 'off'}`\n"
                f"> **Bot add protection:** `{'on' if g.antinuke_botadd else 'off'}`\n\n"
                f"```\n{prefix}antinuke setup enable/disable\n"
                f"{prefix}antinuke kick/ban/vanity/guildupdate/botadd\n"
                f"{prefix}antinuke whitelist add/remove <user>\n"
                f"{prefix}antinuke admin add/remove <user>\n"
                f"{prefix}antinuke admins\n```"
            )
        )

    @antinuke.command(name="setup")
    async def antinuke_setup(self, ctx: "PushieContext", toggle: str) -> None:
        """Enable or disable antinuke."""
        assert ctx.guild is not None
        if toggle.lower() not in ["enable", "disable"]:
            await ctx.err("*Use `enable` or `disable`.*")
            return
        enabled = toggle.lower() == "enable"
        await self.bot.storage.update_setup(ctx.guild.id, antinuke_enabled=enabled)
        state = f"`{Emoji.SUCCESS}` enabled" if enabled else f"`{Emoji.CANCEL}` disabled"
        await ctx.ok(f"*Antinuke {state}.*")

    @antinuke.command(name="kick")
    async def antinuke_kick(self, ctx: "PushieContext") -> None:
        """Toggle mass kick protection."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        g.antinuke_kick = not g.antinuke_kick
        await self.bot.storage.save_guild(g)
        state = "enabled" if g.antinuke_kick else "disabled"
        await ctx.ok(f"*Mass kick protection {state}.*")

    @antinuke.command(name="ban")
    async def antinuke_ban(self, ctx: "PushieContext") -> None:
        """Toggle mass ban protection."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        g.antinuke_ban = not g.antinuke_ban
        await self.bot.storage.save_guild(g)
        state = "enabled" if g.antinuke_ban else "disabled"
        await ctx.ok(f"*Mass ban protection {state}.*")

    @antinuke.command(name="vanity")
    async def antinuke_vanity(self, ctx: "PushieContext") -> None:
        """Toggle vanity URL protection."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        g.antinuke_vanity = not g.antinuke_vanity
        await self.bot.storage.save_guild(g)
        state = "enabled" if g.antinuke_vanity else "disabled"
        await ctx.ok(f"*Vanity protection {state}.*")

    @antinuke.command(name="guildupdate")
    async def antinuke_guildupdate(self, ctx: "PushieContext") -> None:
        """Toggle guild update protection."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        g.antinuke_guildupdate = not g.antinuke_guildupdate
        await self.bot.storage.save_guild(g)
        state = "enabled" if g.antinuke_guildupdate else "disabled"
        await ctx.ok(f"*Guild update protection {state}.*")

    @antinuke.command(name="botadd")
    async def antinuke_botadd(self, ctx: "PushieContext") -> None:
        """Toggle bot add protection."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        g.antinuke_botadd = not g.antinuke_botadd
        await self.bot.storage.save_guild(g)
        state = "enabled" if g.antinuke_botadd else "disabled"
        await ctx.ok(f"*Bot add protection {state}.*")

    @antinuke.group(name="whitelist", invoke_without_command=True)
    async def antinuke_whitelist(self, ctx: "PushieContext") -> None:
        """Antinuke whitelist management."""
        prefix = ctx.prefix or "!"
        await ctx.info(f"Use: `{prefix}antinuke whitelist add <user>` or `{prefix}antinuke whitelist remove <user>`")

    @antinuke_whitelist.command(name="add")
    async def antinuke_whitelist_add(self, ctx: "PushieContext", member: discord.Member) -> None:
        """Add user to antinuke whitelist."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        if member.id not in g.antinuke_whitelist:
            g.antinuke_whitelist.append(member.id)
            await self.bot.storage.save_guild(g)
        await ctx.ok(f"*{member.mention} added to antinuke whitelist.*")

    @antinuke_whitelist.command(name="remove")
    async def antinuke_whitelist_remove(self, ctx: "PushieContext", member: discord.Member) -> None:
        """Remove user from antinuke whitelist."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        if member.id in g.antinuke_whitelist:
            g.antinuke_whitelist.remove(member.id)
            await self.bot.storage.save_guild(g)
        await ctx.ok(f"*{member.mention} removed from antinuke whitelist.*")

    @antinuke.command(name="admins")
    async def antinuke_admins(self, ctx: "PushieContext") -> None:
        """List antinuke admins."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        if not g.antinuke_admins:
            await ctx.info("*No antinuke admins configured.*")
            return
        lines = [f"> <@{uid}>" for uid in g.antinuke_admins]
        await ctx.send(embed=UI.info(f"`{Emoji.LOCK}` **Antinuke Admins**\n\n" + "\n".join(lines)))

    @antinuke.group(name="admin", invoke_without_command=True)
    async def antinuke_admin(self, ctx: "PushieContext") -> None:
        """Antinuke admin management."""
        prefix = ctx.prefix or "!"
        await ctx.info(f"Use: `{prefix}antinuke admin add <user>` or `{prefix}antinuke admin remove <user>`")

    @antinuke_admin.command(name="add")
    async def antinuke_admin_add(self, ctx: "PushieContext", member: discord.Member) -> None:
        """Add antinuke admin."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        if member.id not in g.antinuke_admins:
            g.antinuke_admins.append(member.id)
            await self.bot.storage.save_guild(g)
        await ctx.ok(f"*{member.mention} added as antinuke admin.*")

    @antinuke_admin.command(name="remove")
    async def antinuke_admin_remove(self, ctx: "PushieContext", member: discord.Member) -> None:
        """Remove antinuke admin."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        if member.id in g.antinuke_admins:
            g.antinuke_admins.remove(member.id)
            await self.bot.storage.save_guild(g)
        await ctx.ok(f"*{member.mention} removed from antinuke admins.*")

    # ======== Fake Permissions ========

    @commands.group(name="fakepermissions", aliases=["fakeperms"], invoke_without_command=True)
    @commands.guild_only()
    @commands.has_guild_permissions(administrator=True)
    async def fakepermissions(self, ctx: "PushieContext") -> None:
        """Fake permissions management."""
        prefix = ctx.prefix or "!"
        await ctx.send(
            embed=UI.info(
                f"`{Emoji.LOCK}` **Fake Permissions**\n\n"
                f"```\n{prefix}fakepermissions add <user> <perms>\n"
                f"{prefix}fakepermissions list\n"
                f"{prefix}fakepermissions remove <user>\n```"
            )
        )

    @fakepermissions.command(name="add")
    async def fakepermissions_add(self, ctx: "PushieContext", member: discord.Member, *, perms: str) -> None:
        """Grant fake permissions to a user."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        perm_list = [p.strip() for p in perms.split(",")]
        g.fake_permissions[str(member.id)] = perm_list
        await self.bot.storage.save_guild(g)
        await ctx.ok(f"*Fake permissions granted to {member.mention}: `{', '.join(perm_list)}`*")

    @fakepermissions.command(name="list")
    async def fakepermissions_list(self, ctx: "PushieContext") -> None:
        """List all fake permissions."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        if not g.fake_permissions:
            await ctx.info("*No fake permissions configured.*")
            return
        lines = [f"> <@{uid}>: `{', '.join(perms)}`" for uid, perms in g.fake_permissions.items()]
        await ctx.send(embed=UI.info(f"`{Emoji.LOCK}` **Fake Permissions**\n\n" + "\n".join(lines)))

    @fakepermissions.command(name="remove")
    async def fakepermissions_remove(self, ctx: "PushieContext", member: discord.Member) -> None:
        """Remove fake permissions from a user."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        if str(member.id) in g.fake_permissions:
            del g.fake_permissions[str(member.id)]
            await self.bot.storage.save_guild(g)
            await ctx.ok(f"*Fake permissions removed from {member.mention}.*")
        else:
            await ctx.err(f"*{member.mention} has no fake permissions.*")

    # ======== Antiraid ========

    @commands.group(name="antiraid", invoke_without_command=True)
    @commands.guild_only()
    @commands.has_guild_permissions(administrator=True)
    async def antiraid(self, ctx: "PushieContext") -> None:
        """Antiraid configuration."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        enabled = f"`{Emoji.SUCCESS}` enabled" if g.antiraid_enabled else f"`{Emoji.CANCEL}` disabled"
        prefix = ctx.prefix or "!"
        await ctx.send(
            embed=UI.info(
                f"`{Emoji.LOCK}` **Antiraid** — {enabled}\n\n"
                f"> **Mass mention:** `{'on' if g.antiraid_massmention else 'off'}`\n"
                f"> **Mass join:** `{'on' if g.antiraid_massjoin else 'off'}`\n"
                f"> **Account age:** `{'on' if g.antiraid_age else 'off'}`\n"
                f"> **Default avatar:** `{'on' if g.antiraid_avatar else 'off'}`\n"
                f"> **Unverified bots:** `{'on' if g.antiraid_unverifiedbots else 'off'}`\n\n"
                f"```\n{prefix}antiraid setup enable/disable\n"
                f"{prefix}antiraid username add/remove/list <pattern>\n"
                f"{prefix}antiraid massmention/massjoin/age/avatar/unverifiedbots\n"
                f"{prefix}antiraid whitelist add/remove/view <user>\n```"
            )
        )

    @antiraid.command(name="setup")
    async def antiraid_setup(self, ctx: "PushieContext", toggle: str) -> None:
        """Enable or disable antiraid."""
        assert ctx.guild is not None
        if toggle.lower() not in ["enable", "disable"]:
            await ctx.err("*Use `enable` or `disable`.*")
            return
        enabled = toggle.lower() == "enable"
        await self.bot.storage.update_setup(ctx.guild.id, antiraid_enabled=enabled)
        state = f"`{Emoji.SUCCESS}` enabled" if enabled else f"`{Emoji.CANCEL}` disabled"
        await ctx.ok(f"*Antiraid {state}.*")

    @antiraid.group(name="username", invoke_without_command=True)
    async def antiraid_username(self, ctx: "PushieContext") -> None:
        """Username pattern management."""
        prefix = ctx.prefix or "!"
        await ctx.info(f"Use: `{prefix}antiraid username add <pattern>` / `remove` / `list`")

    @antiraid_username.command(name="add")
    async def antiraid_username_add(self, ctx: "PushieContext", *, pattern: str) -> None:
        """Add username pattern to block."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        if pattern not in g.antiraid_username_patterns:
            g.antiraid_username_patterns.append(pattern)
            await self.bot.storage.save_guild(g)
        await ctx.ok(f"*Added username pattern: `{pattern}`*")

    @antiraid_username.command(name="remove")
    async def antiraid_username_remove(self, ctx: "PushieContext", *, pattern: str) -> None:
        """Remove username pattern."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        if pattern in g.antiraid_username_patterns:
            g.antiraid_username_patterns.remove(pattern)
            await self.bot.storage.save_guild(g)
            await ctx.ok(f"*Removed username pattern: `{pattern}`*")
        else:
            await ctx.err(f"*Pattern `{pattern}` not found.*")

    @antiraid_username.command(name="list")
    async def antiraid_username_list(self, ctx: "PushieContext") -> None:
        """List username patterns."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        if not g.antiraid_username_patterns:
            await ctx.info("*No username patterns configured.*")
            return
        lines = [f"> `{p}`" for p in g.antiraid_username_patterns]
        await ctx.send(embed=UI.info(f"`{Emoji.BLACKLIST}` **Username Patterns**\n\n" + "\n".join(lines)))

    @antiraid.command(name="massmention")
    async def antiraid_massmention(self, ctx: "PushieContext") -> None:
        """Toggle mass mention protection."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        g.antiraid_massmention = not g.antiraid_massmention
        await self.bot.storage.save_guild(g)
        state = "enabled" if g.antiraid_massmention else "disabled"
        await ctx.ok(f"*Mass mention protection {state}.*")

    @antiraid.command(name="massjoin")
    async def antiraid_massjoin(self, ctx: "PushieContext") -> None:
        """Toggle mass join protection."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        g.antiraid_massjoin = not g.antiraid_massjoin
        await self.bot.storage.save_guild(g)
        state = "enabled" if g.antiraid_massjoin else "disabled"
        await ctx.ok(f"*Mass join protection {state}.*")

    @antiraid.command(name="age")
    async def antiraid_age(self, ctx: "PushieContext") -> None:
        """Toggle new account protection (< 7 days)."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        g.antiraid_age = not g.antiraid_age
        await self.bot.storage.save_guild(g)
        state = "enabled" if g.antiraid_age else "disabled"
        await ctx.ok(f"*Account age protection {state}.*")

    @antiraid.command(name="avatar")
    async def antiraid_avatar(self, ctx: "PushieContext") -> None:
        """Toggle default avatar protection."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        g.antiraid_avatar = not g.antiraid_avatar
        await self.bot.storage.save_guild(g)
        state = "enabled" if g.antiraid_avatar else "disabled"
        await ctx.ok(f"*Default avatar protection {state}.*")

    @antiraid.command(name="unverifiedbots")
    async def antiraid_unverifiedbots(self, ctx: "PushieContext") -> None:
        """Toggle unverified bot protection."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        g.antiraid_unverifiedbots = not g.antiraid_unverifiedbots
        await self.bot.storage.save_guild(g)
        state = "enabled" if g.antiraid_unverifiedbots else "disabled"
        await ctx.ok(f"*Unverified bot protection {state}.*")

    @antiraid.group(name="whitelist", invoke_without_command=True)
    async def antiraid_whitelist(self, ctx: "PushieContext") -> None:
        """Antiraid whitelist management."""
        prefix = ctx.prefix or "!"
        await ctx.info(f"Use: `{prefix}antiraid whitelist add/remove/view <user>`")

    @antiraid_whitelist.command(name="add")
    async def antiraid_whitelist_add(self, ctx: "PushieContext", member: discord.Member) -> None:
        """Add user to antiraid whitelist."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        if member.id not in g.antiraid_whitelist:
            g.antiraid_whitelist.append(member.id)
            await self.bot.storage.save_guild(g)
        await ctx.ok(f"*{member.mention} added to antiraid whitelist.*")

    @antiraid_whitelist.command(name="remove")
    async def antiraid_whitelist_remove(self, ctx: "PushieContext", member: discord.Member) -> None:
        """Remove user from antiraid whitelist."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        if member.id in g.antiraid_whitelist:
            g.antiraid_whitelist.remove(member.id)
            await self.bot.storage.save_guild(g)
        await ctx.ok(f"*{member.mention} removed from antiraid whitelist.*")

    @antiraid_whitelist.command(name="view")
    async def antiraid_whitelist_view(self, ctx: "PushieContext") -> None:
        """View antiraid whitelist."""
        assert ctx.guild is not None
        g = await self.bot.storage.get_guild(ctx.guild.id)
        if not g.antiraid_whitelist:
            await ctx.info("*Antiraid whitelist is empty.*")
            return
        lines = [f"> <@{uid}>" for uid in g.antiraid_whitelist]
        await ctx.send(embed=UI.info(f"`{Emoji.WHITELIST}` **Antiraid Whitelist**\n\n" + "\n".join(lines)))

    async def cog_command_error(self, ctx: commands.Context, error: Exception) -> None:
        if isinstance(error, commands.CommandInvokeError):
            error = error.original  # type: ignore
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(embed=UI.error(f"*You need: {', '.join(f'`{p}`' for p in error.missing_permissions)}*"))
        elif isinstance(error, commands.CheckFailure):
            await ctx.send(embed=UI.error(str(error)))
        else:
            raise error


async def setup(bot: "Pushie") -> None:
    await bot.add_cog(Security(bot))
