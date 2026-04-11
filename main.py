from __future__ import annotations

import datetime
import logging
import os
import threading
import traceback
import typing
from pathlib import Path

import aiohttp
import discord
from discord.ext import commands
from dotenv import load_dotenv
from flask import Flask, jsonify

from storage import StorageManager
from ui import UI, PrefixView
from emojis import Emoji
from supabase_client import close_client

log = logging.getLogger("pushie")


# ── CONTEXT & BOT SETUP ────────────────────────────────────────────────────

class PushieContext(commands.Context):
    """Extended context with helper methods for common responses."""

    bot: "Pushie"

    async def ok(self, msg: str) -> discord.Message:
        """Send a success embed."""
        return await self.send(embed=UI.success(msg))

    async def err(self, msg: str) -> discord.Message:
        """Send an error embed."""
        return await self.send(embed=UI.error(msg))

    async def warn(self, msg: str) -> discord.Message:
        """Send a warning embed."""
        return await self.send(embed=UI.warning(msg))

    async def info(self, msg: str) -> discord.Message:
        """Send an info embed."""
        return await self.send(embed=UI.info(msg))


# ── MAIN BOT CLASS ────────────────────────────────────────────────────────

class Pushie(commands.Bot):
    """Main Discord bot with storage, session, and cog management."""

    storage: StorageManager
    session: aiohttp.ClientSession
    _uptime: datetime.datetime

    def __init__(self) -> None:
        """Initialize bot with intents and command settings."""
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        intents.reactions = True
        intents.presences = True

        super().__init__(
            command_prefix=self._get_prefix,
            intents=intents,
            help_command=None,
            case_insensitive=True,
        )

    async def _get_prefix(self, bot: "Pushie", message: discord.Message) -> list[str]:
        """Resolve the command prefix for a message."""
        if not message.guild:
            return commands.when_mentioned_or("!")(bot, message)
        g = bot.storage.get_guild_sync(message.guild.id)
        prefix = g.prefix if g else "!"
        return commands.when_mentioned_or(prefix)(bot, message)

    async def get_context(
        self,
        message: discord.Message | discord.Interaction,
        *,
        cls: type[commands.Context] = PushieContext,
    ) -> PushieContext:
        """Create a PushieContext for commands."""
        return await super().get_context(message, cls=cls)  # type: ignore[return-value]

    # ── INITIALIZATION ──────────────────────────────────────────────────────

    async def setup_hook(self) -> None:
        """Initialize storage, session, and load all cogs."""
        self._uptime = datetime.datetime.now(datetime.UTC)
        self.storage = StorageManager()
        self.session = aiohttp.ClientSession()
        await self.storage.load_all()
        await self._load_cogs()

    async def _load_cogs(self) -> None:
        """Dynamically load all cogs from the cogs directory."""
        cogs_dir = Path("cogs")
        if not cogs_dir.is_dir():
            log.warning("No cogs directory found")
            return
        for path in cogs_dir.glob("*.py"):
            if path.stem.startswith("_"):
                continue
            ext = f"cogs.{path.stem}"
            try:
                await self.load_extension(ext)
                log.info("Loaded %s", ext)
            except commands.ExtensionError:
                log.error("Failed to load %s\n%s", ext, traceback.format_exc())

    async def close(self) -> None:
        """Cleanup session and Supabase client on shutdown."""
        if hasattr(self, "session") and self.session:
            await self.session.close()
        await close_client()
        await super().close()

    # ── PROPERTIES & STATUS ────────────────────────────────────────────────

    @property
    def uptime(self) -> datetime.timedelta:
        """Get bot uptime duration."""
        return datetime.datetime.now(datetime.UTC) - self._uptime

    # ── EVENT HANDLERS ────────────────────────────────────────────────────

    async def on_ready(self) -> None:
        """Initialize bot state and sync slash commands on ready."""
        if self.user:
            log.info(
                "Ready — %s (%s) | %d guilds", self.user, self.user.id, len(self.guilds)
            )
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching, name="over the server 🐱"
            )
        )
        try:
            synced = await self.tree.sync()
            log.info("Synced %d slash commands", len(synced))
        except Exception as e:
            log.error("Failed to sync slash commands: %s", e)

    async def on_guild_join(self, guild: discord.Guild) -> None:
        """Handle bot being added to a guild - reject if banned."""
        if self.storage.is_banned_guild(guild.id):
            log.warning("Joined banned guild %s — leaving", guild.id)
            await guild.leave()
            return
        await self.storage.get_guild(guild.id)
        log.info("Joined guild %s (%s)", guild.name, guild.id)
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                try:
                    await self._send_welcome_message(channel)
                except discord.Forbidden:
                    pass
                break

    async def _send_welcome_message(self, channel: discord.TextChannel) -> None:
        """Send welcome message with instructions to new guild."""
        class WelcomeView(discord.ui.LayoutView):
            container = (
                discord.ui.Container()
                .add_item(
                    discord.ui.MediaGallery(
                        discord.MediaGalleryItem(
                            "https://cdn.discordapp.com/attachments/1462278681962741952/1489981539818410144/download_1.gif?ex=69d264f1&is=69d11371&hm=102f3ce3f7f60bda7be46a78426d697b80074217a303cfff01194e7ef5d3ccc5&"
                        )
                    )
                )
                .add_item(
                    discord.ui.TextDisplay(
                        f"> ### `{Emoji.WELCOME}` Haii thank you for adding me!\n\n"
                    )
                )
                .add_item(
                    discord.ui.Separator(
                        spacing=discord.SeparatorSpacing.large, visible=True
                    )
                )
                .add_item(
                    discord.ui.TextDisplay(
                        f"> `{Emoji.INFO}` *How to use:*\n"
                        f"```\n/help {{module}} {{cmd}}\n```\n"
                        f"> `{Emoji.NEXT}` *Quick setup:* \n"
                        f"```\n/setup --begins setup wizz\n```\n"
                        f"> `{Emoji.ROLE}` *Easy commands:*\n"
                        f"```\n@Pushie - See current prefix \n"
                        f"/prefix new_prefix\n"
                        f"/afk msg\n```"
                    )
                )
            )

        await channel.send(view=WelcomeView())

    async def on_guild_remove(self, guild: discord.Guild) -> None:
        """Log when bot leaves a guild."""
        log.info("Left guild %s (%s)", guild.name, guild.id)

    async def on_message(self, message: discord.Message) -> None:
        """Handle messages: prefix display, AFK tracking, command processing."""
        if message.author.bot:
            return
        if not message.guild:
            await self.process_commands(message)
            return

        if self.user and message.mentions and self.user in message.mentions:
            if len(message.content.split()) == 1:
                g = self.storage.get_guild_sync(message.guild.id)
                current_prefix = g.prefix if g else "!"
                view = PrefixView(bot=self, guild_id=message.guild.id)
                await message.channel.send(
                    embed=UI.info(f"Current prefix: `{current_prefix}`"), view=view
                )
                return

        if self.storage.is_banned_user(message.author.id):
            return

        g = self.storage.get_guild_sync(message.guild.id)
        if g:
            if message.author.id in g.user_blacklist:
                return
            if g.bot_lock and message.author.id not in g.bot_whitelist:
                if not self.storage.is_sudo(message.author.id):
                    return

        if message.mentions and g:
            seen = set()
            for user in message.mentions:
                if user.id in seen:
                    continue
                seen.add(user.id)
                afk = g.afks.get(str(user.id))
                if afk:
                    since = datetime.datetime.utcfromtimestamp(afk["since"])
                    delta = discord.utils.format_dt(since, style="R")
                    await message.channel.send(
                        embed=UI.afk(
                            f"*{user.display_name} is AFK since {delta} — {afk['reason']}*"
                        ),
                        delete_after=10,
                    )

        if g and str(message.author.id) in g.afks:
            afk_info = g.afks[str(message.author.id)]
            afk_since = afk_info.get("since", 0)
            current_time = datetime.datetime.now(datetime.UTC).timestamp()

            if current_time - afk_since > 2:
                prefix = g.prefix if g else "!"
                is_command = message.content.startswith(
                    prefix
                ) or message.content.startswith("/")

                if not is_command:
                    await message.channel.send(
                        embed=UI.success(
                            f"Welcome back {message.author.mention}, AFK cleared."
                        ),
                        delete_after=5,
                    )

            await self.storage.clear_afk(message.guild.id, message.author.id)

        await self.process_commands(message)

    async def on_command_error(  # type: ignore[override]
        self, ctx: commands.Context["Pushie"], error: commands.CommandError
    ) -> None:
        """Handle command errors with user-friendly messages."""
        if hasattr(ctx.command, "on_error"):
            return
        if ctx.cog and ctx.cog.has_error_handler():
            return

        if isinstance(error, commands.CommandNotFound):
            return
        if isinstance(error, commands.NotOwner):
            return

        if not isinstance(error, commands.CommandOnCooldown) and ctx.command:
            ctx.command.reset_cooldown(ctx)

        if isinstance(error, commands.CommandInvokeError):
            error = error.original  # type: ignore[assignment]

        msg: str

        if isinstance(error, commands.MissingRequiredArgument):
            msg = f"Missing argument: `{error.param.name}`"
        elif isinstance(error, commands.BadArgument):
            msg = f"Bad argument: *{error}*"
        elif isinstance(error, commands.CommandOnCooldown):
            msg = f"Cooldown — try again in `{error.retry_after:.1f}s`"
        elif isinstance(error, commands.MissingPermissions):
            perms = ", ".join(f"`{p}`" for p in error.missing_permissions)
            msg = f"You need: {perms}"
        elif isinstance(error, commands.BotMissingPermissions):
            perms = ", ".join(f"`{p}`" for p in error.missing_permissions)
            msg = f"I need: {perms}"
        elif isinstance(error, commands.CheckFailure):
            msg = str(error) or "You can't use this command here."
        elif isinstance(error, commands.DisabledCommand):
            msg = "This command is currently disabled."
        elif isinstance(error, commands.NoPrivateMessage):
            msg = "This command can only be used in a server."
        else:
            tb = "".join(
                traceback.format_exception(type(error), error, error.__traceback__)
            )
            log.error("Unhandled error in %s:\n%s", ctx.command, tb)
            msg = f"An unexpected error occurred.\n```py\n{tb[:1500]}\n```"

        await ctx.send(embed=UI.error(msg))

    async def on_error(
        self, event: str, *args: typing.Any, **kwargs: typing.Any
    ) -> None:
        """Log unhandled errors in event handlers."""
        log.error("Error in event %s:\n%s", event, traceback.format_exc())


def _setup_checks(bot: Pushie) -> None:

    @bot.check
    async def global_banned_guild(ctx: PushieContext) -> bool:
        if ctx.guild and bot.storage.is_banned_guild(ctx.guild.id):
            return False
        return True

    @bot.check
    async def global_banned_user(ctx: PushieContext) -> bool:
        return not bot.storage.is_banned_user(ctx.author.id)


def _setup_flask() -> Flask:
    app = Flask(__name__)

    @app.route("/health", methods=["HEAD", "GET"])
    def health() -> typing.Any:
        return jsonify({"status": "ok"})

    @app.route("/", methods=["HEAD", "GET"])
    def index() -> typing.Any:
        return jsonify({"bot": "Pushie", "status": "running"})

    return app


def is_sudo():
    async def predicate(ctx: PushieContext) -> bool:
        if ctx.bot.storage.is_sudo(ctx.author.id):
            return True
        sudo_user_env = os.getenv("SUDO_USER")
        if sudo_user_env and str(ctx.author.id) == sudo_user_env:
            return True
        raise commands.CheckFailure("You need sudo access to use this command.")

    return commands.check(predicate)


def is_guild_owner():
    async def predicate(ctx: PushieContext) -> bool:
        if ctx.guild and ctx.author.id == ctx.guild.owner_id:
            return True
        raise commands.CheckFailure("You must be the server owner.")

    return commands.check(predicate)


def is_guild_admin():
    async def predicate(ctx: PushieContext) -> bool:
        if ctx.guild and isinstance(ctx.author, discord.Member):
            if ctx.author.guild_permissions.manage_guild:
                return True
        raise commands.CheckFailure("You need Manage Server permission.")

    return commands.check(predicate)


def is_mod():
    async def predicate(ctx: PushieContext) -> bool:
        if ctx.guild and isinstance(ctx.author, discord.Member):
            p = ctx.author.guild_permissions
            if p.kick_members or p.ban_members or p.manage_messages:
                return True
        raise commands.CheckFailure("You need moderator permissions.")

    return commands.check(predicate)


def is_boosting():
    async def predicate(ctx: PushieContext) -> bool:
        if ctx.guild and isinstance(ctx.author, discord.Member):
            if ctx.author.premium_since is not None:
                return True
        raise commands.CheckFailure("You must be a server booster.")

    return commands.check(predicate)


def guild_only():
    async def predicate(ctx: PushieContext) -> bool:
        if ctx.guild:
            return True
        raise commands.CheckFailure("This command can only be used in a server.")

    return commands.check(predicate)


def dm_only():
    async def predicate(ctx: PushieContext) -> bool:
        if not ctx.guild:
            return True
        raise commands.CheckFailure("This command can only be used in DMs.")

    return commands.check(predicate)


def in_voice():
    async def predicate(ctx: PushieContext) -> bool:
        if ctx.author.voice and ctx.author.voice.channel:  # type: ignore
            return True
        raise commands.CheckFailure("You need to be in a voice channel.")

    return commands.check(predicate)


def main() -> None:
    load_dotenv()
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    app = _setup_flask()
    port = int(os.getenv("PORT", 5000))
    flask_thread = threading.Thread(
        target=lambda: app.run(host="0.0.0.0", port=port, debug=False),
        daemon=True,
    )
    flask_thread.start()
    log.info("Flask health endpoint started on port %d", port)

    bot = Pushie()
    _setup_checks(bot)
    token = os.getenv("TOKEN")
    if not token:
        log.critical("TOKEN not set in .env")
        raise SystemExit(1)
    try:
        bot.run(token, log_handler=None)
    except (discord.LoginFailure, KeyboardInterrupt):
        log.info("Shutting down")


if __name__ == "__main__":
    main()
