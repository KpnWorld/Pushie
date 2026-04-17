from __future__ import annotations


class Emoji:
    """Named emoji constants for the entire bot.

    Usage example:
        from emojis import Emoji
        embed = discord.Embed(description=f"> {Emoji.SUCCESS} *Action completed*")
    """

    # ── RESPONSE STATUS ─────────────────────────────────────────────────────
    SUCCESS = "<:check:1494837797977063424>"
    ERROR = "<:deny:1494837797293391935>"
    WARNING = "<:warning:1494837848375951401>"
    INFO = "<:info:1494837821025026170>"
    LOADING = "<a:load:1494837860204023909>"

    # ── MODERATION ──────────────────────────────────────────────────────────
    JAIL = "🔒"
    UNJAIL = "🔓"
    KICK = "👢"
    BAN = "🔨"
    UNBAN = "✅"
    TIMEOUT = "⏰"
    UNTIMEOUT = "⏲"
    AFK = "💤"
    MUTE = "🔇"
    UNMUTE = "🔊"
    IMUTE = "🖼"
    RMUTE = "🚫"
    WARN = "⚠"
    CLEAR = "🧹"
    HIDE = "👁"
    UNHIDE = "👁"
    SLOWMODE = "🐌"
    PURGE = "🗑"
    NICK = "📝"
    RESET = "🔄"

    # ── SETUP & CONFIGURATION ───────────────────────────────────────────────
    SETUP = "⚙"
    CHANNEL = "📢"
    SYNC = "🔁"
    ROLE = "🏷"

    # ── WELCOME & ROLES ─────────────────────────────────────────────────────
    WELCOME = "👋"
    AUTOROLE = "⭐"
    BOOSTER = "🚀"

    # ── PAGINATION & NAVIGATION ─────────────────────────────────────────────
    PREV = "◂"
    NEXT = "▸"
    GOTO = "◆"
    FIRST = "⏪"
    LAST = "⏩"
    STOP = "🗑"

    # ── ACTIONS ─────────────────────────────────────────────────────────────
    CONFIRM = "✓"
    CANCEL = "✕"
    PING = "🏓"
    HEART = "💖"
    PUSHEEN = "🐱"
    STICKY = "📌"

    # ── ADMIN & SUDO ────────────────────────────────────────────────────────
    SUDO = "🛠"
    COG = "📦"
    RESTART = "🔄"
    STATS = "📊"

    # ── EVENTS ──────────────────────────────────────────────────────────────
    JOIN = "📥"
    LEAVE = "📤"
    EDIT = "📝"
    DELETE = "🗑"

    # ── SECURITY ────────────────────────────────────────────────────────────
    LOCK = "🔐"
    UNLOCK = "🔓"
    WHITELIST = "✅"
    BLACKLIST = "🚫"

    # ── EMBEDS & MODALS ─────────────────────────────────────────────────────
    EMBED = "📋"
    MODAL = "📝"

    REACTION = "🔄"

    IMAGE = "🖼"
    DOWNLOAD = "⬇"

    @classmethod
    def code(cls, emoji: str) -> str:
        """Returns emoji wrapped in backticks for the UI style."""
        return f"`{emoji}`"
