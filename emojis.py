# emoji.py
# Central emoji registry for Pushie Pusheen
# All emojis used in UI, responses, modals, paginators, etc. live here
# Never hardcode an emoji anywhere else in the bot

from __future__ import annotations


class Emoji:
    """Named emoji constants for the entire bot.

    Usage example:
        from emoji import Emoji
        embed = discord.Embed(description=f"> {Emoji.SUCCESS} *Action completed*")
    """

    # Status / UI
    SUCCESS = "☑️"
    ERROR = "❌"
    WARNING = "⚠️"
    INFO = "ℹ️"
    LOADING = "⏳"

    # Moderation
    JAIL = "🔒"
    UNJAIL = "🔓"
    KICK = "👢"
    BAN = "🔨"
    UNBAN = "✅"
    TIMEOUT = "⏰"
    UNTIMEOUT = "⏲️"
    AFK = "💤"
    MUTE = "🔇"
    UNMUTE = "🔊"
    IMUTE = "🖼️"
    RMUTE = "🚫"
    WARN = "⚠️"
    CLEAR = "🧹"
    HIDE = "👁️‍🗨️"
    UNHIDE = "👁️"
    SLOWMODE = "🐌"
    PURGE = "🗑️"
    NICK = "📝"
    RESET = "🔄"

    # Setup
    SETUP = "⚙️"
    CHANNEL = "📢"
    SYNC = "🔁"

    # Roles & Welcome
    ROLE = "🏷️"
    WELCOME = "👋"
    AUTOROLE = "⭐"
    BOOSTER = "🚀"

    # Pagination (exactly as requested)
    PREV = "◂"
    NEXT = "▸"
    GOTO = "◆"
    FIRST = "⏪"
    LAST = "⏩"
    STOP = "🗑️"

    # Confirmation prompts
    CONFIRM = "✓"
    CANCEL = "✕"

    # Misc / Fun
    PING = "🏓"
    HEART = "💖"
    PUSHEEN = "🐱"  # main bot mascot emoji
    STICKY = "📌"

    # Commands / Sudo
    SUDO = "🛠️"
    COG = "📦"
    RESTART = "🔄"
    STATS = "📊"

    # Log events
    JOIN = "📥"
    LEAVE = "📤"
    EDIT = "📝"
    DELETE = "🗑️"

    # Bot access
    LOCK = "🔐"
    UNLOCK = "🔓"
    WHITELIST = "✅"
    BLACKLIST = "🚫"

    # Embed / Modal
    EMBED = "📋"
    MODAL = "📝"

    # Reaction roles
    REACTION = "🔄"

    # Info / Images
    IMAGE = "🖼️"
    DOWNLOAD = "⬇️"

    @classmethod
    def code(cls, emoji: str) -> str:
        """Returns emoji wrapped in backticks for the UI style."""
        return f"`{emoji}`"
