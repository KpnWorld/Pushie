from __future__ import annotations


class Emoji:
    """Named emoji constants for the entire bot.

    Usage example:
        from emojis import Emoji
        embed = discord.Embed(description=f"> {Emoji.SUCCESS} *Action completed*")
    """

    # ── RESPONSE STATUS ─────────────────────────────────────────────────────
    SUCCESS = "☑"
    ERROR = "❌"
    WARNING = "⚠"
    INFO = "ℹ"
    LOADING = "⏳"

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
