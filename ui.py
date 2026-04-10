from __future__ import annotations

import re
import traceback
import datetime
from typing import Any

import discord
from discord.ui.select import BaseSelect
from emojis import Emoji

COLOR = 0xFAB9EC


def _base(msg: str, emoji: str) -> discord.Embed:
    return discord.Embed(description=f"> `{emoji}` *{msg}*", color=COLOR)


class UI:

    @staticmethod
    def success(msg: str) -> discord.Embed:
        return _base(msg, Emoji.SUCCESS)

    @staticmethod
    def error(msg: str) -> discord.Embed:
        return _base(msg, Emoji.ERROR)

    @staticmethod
    def warning(msg: str) -> discord.Embed:
        return _base(msg, Emoji.WARNING)

    @staticmethod
    def info(msg: str) -> discord.Embed:
        return _base(msg, Emoji.INFO)

    @staticmethod
    def afk(msg: str) -> discord.Embed:
        return _base(msg, Emoji.AFK)

    @staticmethod
    def loading(msg: str) -> discord.Embed:
        return _base(msg, Emoji.LOADING)

    @staticmethod
    def confirm(msg: str) -> discord.Embed:
        return _base(msg, Emoji.WARNING).set_footer(
            text=f"{Emoji.CONFIRM} confirm  ·  {Emoji.CANCEL} cancel"
        )

    @staticmethod
    def paginator(msg: str, page: int, total: int) -> discord.Embed:
        return _base(msg, Emoji.INFO).set_footer(
            text=f"page {page}/{total}  ·  {Emoji.PREV} prev  {Emoji.NEXT} next  {Emoji.GOTO} goto"
        )

    @staticmethod
    def welcome() -> discord.Embed:
        """Welcome embed for new bot joins."""
        embed = discord.Embed(
            description=f"> ### `{Emoji.WELCOME}` Haii thank you for adding me!",
            color=COLOR,
        )
        embed.add_field(
            name="",
            value=f"> `{Emoji.INFO}` *How to use:*\n```\n/help {{module}} {{cmd}}\n```\n> `{Emoji.NEXT}` *Quick setup:* \n```\n/setup --begins setup wizz\n```\n> `{Emoji.ROLE}` *Easy commands:*\n```\n@Pushie - See current prefix \n/prefix new_prefix\n/afk msg\n```",
            inline=False,
        )
        return embed


class BaseView(discord.ui.View):
    interaction: discord.Interaction | None = None
    message: discord.Message | None = None

    def __init__(self, user: discord.User | discord.Member, timeout: float = 60.0):
        super().__init__(timeout=timeout)
        self.user = user

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user.id:
            await interaction.response.send_message(
                embed=UI.error("This isn't your interaction."), ephemeral=True
            )
            return False
        self.interaction = interaction
        return True

    def _disable_all(self) -> None:
        for item in self.children:
            if isinstance(item, (discord.ui.Button, BaseSelect)):
                item.disabled = True

    async def _edit(self, **kwargs: Any) -> None:
        try:
            if self.message is not None:
                await self.message.edit(**kwargs)
            elif self.interaction is not None:
                if not self.interaction.response.is_done():
                    await self.interaction.response.edit_message(**kwargs)
                else:
                    await self.interaction.edit_original_response(**kwargs)
        except (discord.NotFound, discord.HTTPException):
            pass

    async def on_error(
        self, interaction: discord.Interaction, error: Exception, item: discord.ui.Item
    ) -> None:
        tb = "".join(
            traceback.format_exception(type(error), error, error.__traceback__)
        )
        self._disable_all()
        await self._edit(
            embed=UI.error(f"An error occurred.\n```py\n{tb[:1800]}\n```"), view=self
        )
        self.stop()

    async def on_timeout(self) -> None:
        self._disable_all()
        await self._edit(view=self)


class ChangePrefix(discord.ui.Modal):
    """Modal for changing the server prefix."""

    prefix = discord.ui.TextInput(
        label="New Prefix",
        placeholder="e.g. !",
        min_length=1,
        max_length=10,
    )

    def __init__(self, bot: Any, guild_id: int) -> None:
        super().__init__(title="Set Server Prefix")
        self._bot = bot
        self._guild_id = guild_id

    async def on_submit(self, interaction: discord.Interaction) -> None:
        new_prefix = self.prefix.value.strip()
        await interaction.response.defer(ephemeral=True)
        await self._bot.storage.set_prefix(self._guild_id, new_prefix)
        await interaction.followup.send(
            embed=UI.success(f"Prefix changed to `{new_prefix}`"),
            ephemeral=True,
        )
        self.stop()

    async def on_error(
        self, interaction: discord.Interaction, error: Exception
    ) -> None:
        await interaction.response.send_message(
            embed=UI.error("Failed to update prefix."), ephemeral=True
        )
        self.stop()


class PrefixView(discord.ui.View):
    """View with button to change prefix."""

    def __init__(self, bot: Any | None = None, guild_id: int | None = None):
        super().__init__(timeout=300)
        self._bot = bot
        self._guild_id = guild_id

    @discord.ui.button(label="Change Prefix", style=discord.ButtonStyle.primary)
    async def change_prefix(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        if not self._bot or not self._guild_id:
            await interaction.response.send_message(
                embed=UI.error(
                    "This button has no context — use `/prefix new_prefix` instead."
                ),
                ephemeral=True,
            )
            return
        modal = ChangePrefix(self._bot, self._guild_id)
        await interaction.response.send_modal(modal)


class ConfirmView(BaseView):
    def __init__(self, user: discord.User | discord.Member, timeout: float = 30.0):
        super().__init__(user, timeout)
        self.value: bool | None = None

    @discord.ui.button(label=Emoji.CONFIRM, style=discord.ButtonStyle.success)
    async def confirm(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        self.value = True
        self._disable_all()
        await self._edit(embed=UI.success("Confirmed."), view=self)
        self.stop()

    @discord.ui.button(label=Emoji.CANCEL, style=discord.ButtonStyle.danger)
    async def cancel(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        self.value = False
        self._disable_all()
        await self._edit(embed=UI.error("Cancelled."), view=self)
        self.stop()


class BaseModal(discord.ui.Modal):
    _interaction: discord.Interaction | None = None

    async def on_submit(self, interaction: discord.Interaction) -> None:
        if not interaction.response.is_done():
            await interaction.response.defer()
        self._interaction = interaction
        self.stop()

    async def on_error(
        self, interaction: discord.Interaction, error: Exception
    ) -> None:
        tb = "".join(
            traceback.format_exception(type(error), error, error.__traceback__)
        )
        try:
            await interaction.response.send_message(
                embed=UI.error(f"Modal error.\n```py\n{tb[:1800]}\n```"), ephemeral=True
            )
        except discord.InteractionResponded:
            await interaction.edit_original_response(
                embed=UI.error(f"Modal error.\n```py\n{tb[:1800]}\n```")
            )
        self.stop()

    @property
    def interaction(self) -> discord.Interaction | None:
        return self._interaction


class EmbedBuilderModal(BaseModal, title="Embed Builder"):
    content = discord.ui.TextInput(
        label="Content (body text)",
        placeholder="Supports **bold**, *italic*, `code`, {user.mention}, {guild.name} …",
        style=discord.TextStyle.long,
        max_length=4000,
    )
    embed_title = discord.ui.TextInput(
        label="Title (optional)",
        required=False,
        max_length=256,
    )
    footer_text = discord.ui.TextInput(
        label="Footer text (optional)",
        required=False,
        max_length=2048,
    )
    footer_icon = discord.ui.TextInput(
        label="Footer icon URL (optional)",
        placeholder="https://…",
        required=False,
        max_length=500,
    )
    embed_color = discord.ui.TextInput(
        label="Color hex (optional, e.g. FAB9EC)",
        placeholder="FAB9EC",
        required=False,
        max_length=7,
    )

    def build(self, ctx_vars: dict[str, str] | None = None) -> discord.Embed:
        cv = ctx_vars or {}
        description = substitute(self.content.value, cv)
        title = substitute(self.embed_title.value or "", cv) or None
        footer = substitute(self.footer_text.value or "", cv) or None
        ficon = self.footer_icon.value.strip() or None
        raw_color = self.embed_color.value.strip().lstrip("#")
        try:
            color = int(raw_color, 16) if raw_color else COLOR
        except ValueError:
            color = COLOR
        embed = discord.Embed(description=description or None, color=color)
        if title:
            embed.title = title
        if footer:
            embed.set_footer(text=footer, icon_url=ficon)
        return embed


# duration  e.g. "10m" "2h" "1d"
_DURATION_RE = re.compile(r"^(\d+)([smhdw])$")
_DURATION_MAP = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800}


def parse_duration(argument: str) -> datetime.timedelta | None:
    m = _DURATION_RE.match(argument.lower().strip())
    if not m:
        return None
    return datetime.timedelta(seconds=int(m.group(1)) * _DURATION_MAP[m.group(2)])


# ── Inline Embed Parser ───────────────────────────────────────────────────────
#
# Supported input modes for any [input] argument:
#
#   $im <text>          → plain message, no embed wrapper
#   $em [flags…]        → inline embed built from flags (see below)
#   embed  (alone)      → caller should open the EmbedBuilderModal via a button
#   <anything else>     → plain text (caller wraps in UI.info/success/etc.)
#
# Inline embed flags (can appear in any order after $em):
#   $title  <text>      → embed title
#   $color  <hex>       → embed color  (alias: $colour)
#   $footer <text>      → footer text
#   $footericon <url>   → footer icon URL  (alias: $ficon)
#   $author <text>      → author name
#   $authoricon <url>   → author icon URL  (alias: $aicon)
#   $url    <url>       → title hyperlink URL
#   $image  <url>       → large embed image  (alias: $img)
#   $thumbnail <url>    → thumbnail image    (alias: $thumb)
#
# Example:
#   !greet message $em Welcome {user.mention}! $title Hello $footer Pushie Bot $footericon https://…

_FLAG_SPLIT_RE = re.compile(r"\$(\w+)")

# Aliases → canonical key
_FLAG_ALIASES: dict[str, str] = {
    "colour": "color",
    "ficon": "footericon",
    "aicon": "authoricon",
    "img": "image",
    "thumb": "thumbnail",
}


def _split_flags(text: str) -> dict[str, str]:
    """Split '$key value $key2 value2 …' text into a dict."""
    parts = _FLAG_SPLIT_RE.split(text.strip())
    out: dict[str, str] = {}
    # parts[0] is the text *before* the first flag (usually empty for $em …)
    if parts[0].strip():
        out["_prefix"] = parts[0].strip()
    for i in range(1, len(parts), 2):
        key = parts[i].lower()
        key = _FLAG_ALIASES.get(key, key)
        val = parts[i + 1].strip() if i + 1 < len(parts) else ""
        out[key] = val
    return out


class ParsedInput:
    """Result of parse_input(). Describes what a command's [input] arg resolved to."""

    __slots__ = ("kind", "text", "embed")

    def __init__(
        self,
        kind: str,
        text: str | None = None,
        embed: discord.Embed | None = None,
    ) -> None:
        self.kind = kind    # "text" | "plain" | "embed" | "modal"
        self.text = text
        self.embed = embed

    def __repr__(self) -> str:
        return f"<ParsedInput kind={self.kind!r}>"


def parse_input(argument: str, ctx_vars: dict[str, str] | None = None) -> ParsedInput:
    """
    Parse a freeform [input] argument.

    Returns a ParsedInput with one of four kinds:
      "plain"  → send as raw text (no embed)
      "embed"  → send the .embed object
      "modal"  → caller must open EmbedBuilderModal via a button View
      "text"   → plain text string; caller decides how to wrap it
    """
    stripped = argument.strip()
    cv = ctx_vars or {}
    low = stripped.lower()

    # ── $im → plain text, no embed wrapper ───────────────────────────────────
    if low.startswith("$im"):
        content = stripped[3:].strip()
        return ParsedInput(kind="plain", text=substitute(content, cv))

    # ── "embed" alone → modal trigger ─────────────────────────────────────────
    if low in ("embed", "$em"):
        return ParsedInput(kind="modal")

    # ── $em <flags> → inline embed ────────────────────────────────────────────
    if low.startswith("$em"):
        flags = _split_flags(stripped)
        body = substitute(flags.get("em", ""), cv)
        title = substitute(flags.get("title", ""), cv) or None
        footer = substitute(flags.get("footer", ""), cv) or None
        footer_icon = flags.get("footericon", "") or None
        author = substitute(flags.get("author", ""), cv) or None
        author_icon = flags.get("authoricon", "") or None
        url = flags.get("url", "") or None
        image = flags.get("image", "") or None
        thumbnail = flags.get("thumbnail", "") or None
        raw_color = flags.get("color", "").lstrip("#")
        try:
            color = int(raw_color, 16) if raw_color else COLOR
        except ValueError:
            color = COLOR

        embed = discord.Embed(description=body or None, color=color)
        if title:
            embed.title = title
            if url:
                embed.url = url
        if footer:
            embed.set_footer(text=footer, icon_url=footer_icon)
        if author:
            embed.set_author(name=author, icon_url=author_icon)
        if image:
            embed.set_image(url=image)
        if thumbnail:
            embed.set_thumbnail(url=thumbnail)
        return ParsedInput(kind="embed", embed=embed)

    # ── plain text fallback ───────────────────────────────────────────────────
    return ParsedInput(kind="text", text=substitute(stripped, cv))


class EmbedBuilderView(BaseView):
    """
    Sends a button that opens EmbedBuilderModal.
    Pass an async `on_build(embed, interaction)` callback to receive the result.
    """

    def __init__(
        self,
        user: discord.User | discord.Member,
        on_build: Any,
        ctx_vars: dict[str, str] | None = None,
    ) -> None:
        super().__init__(user, timeout=120.0)
        self._on_build = on_build
        self._ctx_vars = ctx_vars or {}

    @discord.ui.button(label="Open Embed Builder", style=discord.ButtonStyle.primary, emoji="✏️")
    async def open_builder(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        modal = EmbedBuilderModal()
        await interaction.response.send_modal(modal)
        await modal.wait()
        if modal.interaction:
            embed = modal.build(self._ctx_vars)
            await self._on_build(embed, modal.interaction)
        self.stop()


# Backwards-compat stubs (kept so any existing import doesn't break)
def is_embed_flag(argument: str) -> bool:
    return argument.strip().lower().startswith("$em")

def is_modal_flag(argument: str) -> bool:
    return argument.strip().lower() in ("embed", "$em")

def strip_embed_flag(argument: str) -> str:
    return argument.strip()[3:].strip()


# variable substitution for welcome msgs, sticky, autoresponders
_VAR_RE = re.compile(r"\{(\w+(?:\.\w+)*)\}")


def substitute(template: str, variables: dict[str, str]) -> str:
    def replacer(match: re.Match) -> str:
        return variables.get(match.group(1)) or match.group(0)

    return _VAR_RE.sub(replacer, template)


def build_ctx_vars(
    guild: discord.Guild,
    member: discord.Member | None = None,
) -> dict[str, str]:
    # called whenever we need to resolve template variables
    vars: dict[str, str] = {
        "guild.name": guild.name,
        "guild.count": str(guild.member_count or 0),
        "guild.owner": guild.owner.mention if guild.owner else "",
        "guild.icon": str(guild.icon.url) if guild.icon else "",
    }
    if member:
        vars.update(
            {
                "user.mention": member.mention,
                "user.name": member.display_name,
                "user.avatar": str(member.display_avatar.url),
            }
        )
    return vars
