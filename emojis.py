from __future__ import annotations


class Emoji:
    """Named emoji constants for the entire bot.

    Usage example:
        from emojis import Emoji
        embed = discord.Embed(description=f"> {Emoji.SUCCESS} *Action completed*")
    """

    # ── RESPONSE STATUS ─────────────────────────────────────────────────────
    SUCCESS = "<:ok:1495556905282834452>"
    ERROR = "<:deny:1494837797293391935>"
    WARNING = "<:warning:1495556935422836766>"
    INFO = "<:info:1495556897435156621>"
    LOADING = "<a:load:1495567736917463100>"

    # ── MODERATION ──────────────────────────────────────────────────────────
    JAIL = "🔒"
    UNJAIL = "<:unlock:1495556931966992445>"
    KICK = "<:kick:1495556897917370415>"
    BAN = "<:ban:1495556880247029842>"
    UNBAN = ""
    TIMEOUT = "<:time:1495556928783384738>"
    UNTIMEOUT = "<:time:1495556928783384738>"
    AFK = "<:afk:1495556875838685334>"
    MUTE = "<:mute:1495556904318009425>"
    UNMUTE = "<:voice:1495556932705194114>"
    IMUTE = "🖼"
    RMUTE = "🚫"
    WARN = "<:warn:1495556934516998205>"
    CLEAR = "<:trash:1495556930754842734>"
    HIDE = "<:hide:1495556895694520430>"
    UNHIDE = "<:show:1495556921397084261>"
    SLOWMODE = "<:snail:1495556922978341104>"
    PURGE = "<:delete:1495556882855890984>"
    NICK = "<:edit:1495556885544177724>"
    RESET = "<:restart:1495556910395428906>"

    # ── SETUP & CONFIGURATION ───────────────────────────────────────────────
    SETUP = "<:config:1495556881962504262>"
    CHANNEL ="<:embed:1495556886425112706>"
    SYNC = "<:sync:1495556927772692512>"
    ROLE = "<:role:1495556911200731376>"

    # ── WELCOME & ROLES ─────────────────────────────────────────────────────
    WELCOME = "👋"
    AUTOROLE = "<:role:1495556911200731376>"
    BOOSTER = "<:star:1495556924727492800>"

    # ── PAGINATION & NAVIGATION ─────────────────────────────────────────────
    PREV = "<:back:1495556877797429488>"
    NEXT = "<:foward:1495556893693837472>"
    GOTO = "<:local:1495556901176475648>"
    FIRST = "⏪"
    LAST = "<:last:1495556898966081536>"
    STOP = "<:stop:1495556927013261484>"

    # ── ACTIONS ─────────────────────────────────────────────────────────────
    CONFIRM = "<:ok:1495556905282834452>"
    CANCEL = "<:cancel:1495556881438216262>"
    PING = "<:ping:1495556907123998760>"
    HEART = "💖"
    PUSHEEN = "🐱"
    STICKY = "<:ping:1495556907123998760>"

    # ── ADMIN & SUDO ────────────────────────────────────────────────────────
    SUDO = "<:config:1495556881962504262>"
    COG = "<:script:1495556912324939917>"
    RESTART = "<:restart:1495556910395428906>"
    STATS = "<:stats:1495556926015275158>"

    # ── EVENTS ──────────────────────────────────────────────────────────────
    JOIN = "📥"
    LEAVE = "📤"
    EDIT = "<:edit:1495556885544177724>"
    DELETE = "<:delete:1495556882855890984>"

    # ── SECURITY ────────────────────────────────────────────────────────────
    LOCK = "<:lock:1495556902120067092>"
    UNLOCK = "<:lock:1495556902120067092>"
    WHITELIST = "<:ok:1495556905282834452>"
    BLACKLIST = "<:wall:1495556933501845626>"

    # ── EMBEDS & MODALS ─────────────────────────────────────────────────────
    EMBED = "<:embed:1495556886425112706>"
    MODAL = "📝"

    REACTION = ""

    IMAGE = "<:image:1495556896570998844>"
    DOWNLOAD = "<:download:1495556884608978964>"

    @classmethod
    def code(cls, emoji: str) -> str:
        """Returns emoji wrapped in backticks for the UI style."""
        return f"{emoji}"
