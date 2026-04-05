from __future__ import annotations


class Emoji:
    """Named emoji constants for the entire bot.

    Usage example:
        from emoji import Emoji
        embed = discord.Embed(description=f"> {Emoji.SUCCESS} *Action completed*")
    """

    SUCCESS = "☑"
    ERROR = "❌"
    WARNING = "⚠"
    INFO = "ℹ"
    LOADING = "⏳"

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

    SETUP = "⚙"
    CHANNEL = "📢"
    SYNC = "🔁"

    ROLE = "🏷"
    WELCOME = "👋"
    AUTOROLE = "⭐"
    BOOSTER = "🚀"

    PREV = "◂"
    NEXT = "▸"
    GOTO = "◆"
    FIRST = "⏪"
    LAST = "⏩"
    STOP = "🗑"

    CONFIRM = "✓"
    CANCEL = "✕"

    PING = "🏓"
    HEART = "💖"
    PUSHEEN = "🐱"  # main bot mascot emoji
    STICKY = "📌"

    SUDO = "🛠"
    COG = "📦"
    RESTART = "🔄"
    STATS = "📊"

    JOIN = "📥"
    LEAVE = "📤"
    EDIT = "📝"
    DELETE = "🗑"

    LOCK = "🔐"
    UNLOCK = "🔓"
    WHITELIST = "✅"
    BLACKLIST = "🚫"

    EMBED = "📋"
    MODAL = "📝"

    REACTION = "🔄"

    IMAGE = "🖼"
    DOWNLOAD = "⬇"

    @classmethod
    def code(cls, emoji: str) -> str:
        """Returns emoji wrapped in backticks for the UI style."""
        return f"`{emoji}`"
