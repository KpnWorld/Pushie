from __future__ import annotations

import datetime
import logging
import os
import traceback
import typing
from pathlib import Path

import aiohttp
import discord
from discord.ext import commands
from dotenv import load_dotenv

from storage import StorageManager
from ui import UI, PrefixView
from emojis import Emoji

log = logging.getLogger("pushie")


class PushieContext(commands.Context):
    bot: "Pushie"

    async def ok(self, msg: str) -> discord.Message:
        return await self.send(embed=UI.success(msg))

    async def err(self, msg: str) -> discord.Message:
        return await self.send(embed=UI.error(msg))

    async def warn(self, msg: str) -> discord.Message:
        return await self.send(embed=UI.warning(msg))

    async def info(self, msg: str) -> discord.Message:
        return await self.send(embed=UI.info(msg))


class Pushie(commands.Bot):
    storage: StorageManager
    session: aiohttp.ClientSession
    _uptime: datetime.datetime

    def __init__(self) -> None:
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
        return await super().get_context(message, cls=cls)  # type: ignore[return-value]

    async def setup_hook(self) -> None:
        self._uptime = datetime.datetime.now(datetime.UTC)
        self.storage = StorageManager()
        self.session = aiohttp.ClientSession()
        await self.storage.load_all()
        await self._load_cogs()

    async def _load_cogs(self) -> None:
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
        await self.session.close()
        await super().close()

    @property
    def uptime(self) -> datetime.timedelta:
        return datetime.datetime.now(datetime.UTC) - self._uptime

    async def on_ready(self) -> None:
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
        log.info("Left guild %s (%s)", guild.name, guild.id)

    async def on_message(self, message: discord.Message) -> None:
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
            for user in message.mentions:
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
            await self.storage.clear_afk(message.guild.id, message.author.id)
            await message.channel.send(
                embed=UI.success(
                    f"Welcome back {message.author.mention}, AFK cleared."
                ),
                delete_after=5,
            )

        await self.process_commands(message)

    async def on_command_error(  # type: ignore[override]
        self, ctx: commands.Context["Pushie"], error: commands.CommandError
    ) -> None:
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


def _setup_commands(bot: Pushie) -> None:

    @bot.hybrid_command(name="ping", description="Check bot latency")
    async def ping(ctx: PushieContext) -> None:
        await ctx.send(
            embed=UI.info(f"`{Emoji.PING}` *Pong! `{round(bot.latency * 1000)}ms`*")
        )

    @bot.hybrid_command(name="afk", description="Set your AFK status")
    async def afk(ctx: PushieContext, *, reason: str = "AFK") -> None:
        if not ctx.guild:
            return
        import time

        await bot.storage.set_afk(ctx.guild.id, ctx.author.id, reason, time.time())
        await ctx.send(embed=UI.afk(f"*{ctx.author.mention} is now AFK — {reason}*"))

    @bot.hybrid_command(name="help", description="Show help")
    async def help_cmd(ctx: PushieContext, *, command: str | None = None) -> None:
        if command:
            cmd = bot.get_command(command)
            if not cmd:
                await ctx.err(f"Command `{command}` not found.")
                return
            syntax = (
                f"/{command}"
                if any(str(c) == command for c in bot.tree._get_all_commands())
                else f"!{command}"
            )
            await ctx.send(
                embed=UI.info(
                    f"`{cmd.name}` — *{cmd.help or 'No description.'}*\n\n```\n{syntax}\n```"
                )
            )
            return
        cog_names = ", ".join(f"`{name}`" for name in bot.cogs)
        help_text = (
            f"*Loaded modules: {cog_names or 'none'}*\n\n"
            f"**Core Commands:**\n"
            f"```\n/ping\n/afk <reason>\n/help [command]\n/prefix [new_prefix]\n```\n\n"
            f"Use `!help <command>` for details."
        )
        await ctx.send(embed=UI.info(help_text))

    @bot.hybrid_command(name="prefix", description="Show or change server prefix")
    async def prefix_cmd(ctx: PushieContext, *, new_prefix: str | None = None) -> None:
        if not ctx.guild:
            return

        if new_prefix:
            if not (
                ctx.guild
                and isinstance(ctx.author, discord.Member)
                and ctx.author.guild_permissions.manage_guild
            ):
                await ctx.err("You need Manage Server permission to change the prefix.")
                return

            await bot.storage.set_prefix(ctx.guild.id, new_prefix)
            await ctx.ok(f"Prefix changed to `{new_prefix}`")
            return

        g = bot.storage.get_guild_sync(ctx.guild.id)
        current_prefix = g.prefix if g else "!"
        view = PrefixView(bot=bot, guild_id=ctx.guild.id)
        await ctx.send(embed=UI.info(f"Current prefix: `{current_prefix}`"), view=view)

    @bot.group(name="sudo", invoke_without_command=True)
    @is_sudo()
    async def sudo_group(ctx: PushieContext) -> None:
        await ctx.info(f"`{Emoji.SUDO}` *Sudo group — use a subcommand.*")

    @sudo_group.command(name="reload")
    @is_sudo()
    async def sudo_reload(ctx: PushieContext, ext: str) -> None:
        try:
            await bot.reload_extension(f"cogs.{ext}")
            await ctx.ok(f"`{Emoji.COG}` *Reloaded `{ext}`*")
        except commands.ExtensionError as e:
            await ctx.err(str(e))

    @sudo_group.command(name="load")
    @is_sudo()
    async def sudo_load(ctx: PushieContext, ext: str) -> None:
        try:
            await bot.load_extension(f"cogs.{ext}")
            await ctx.ok(f"`{Emoji.COG}` *Loaded `{ext}`*")
        except commands.ExtensionError as e:
            await ctx.err(str(e))

    @sudo_group.command(name="unload")
    @is_sudo()
    async def sudo_unload(ctx: PushieContext, ext: str) -> None:
        try:
            await bot.unload_extension(f"cogs.{ext}")
            await ctx.ok(f"`{Emoji.COG}` *Unloaded `{ext}`*")
        except commands.ExtensionError as e:
            await ctx.err(str(e))

    @sudo_group.command(name="sync")
    @is_sudo()
    async def sudo_sync(ctx: PushieContext) -> None:
        synced = await bot.tree.sync()
        await ctx.ok(f"`{Emoji.COG}` *Synced `{len(synced)}` slash commands globally.*")

    @sudo_group.command(name="stats")
    @is_sudo()
    async def sudo_stats(ctx: PushieContext) -> None:
        import psutil, os as _os

        proc = psutil.Process(_os.getpid())
        mem = proc.memory_info().rss / 1024 / 1024
        cpu = proc.cpu_percent(interval=0.1)
        up = str(bot.uptime).split(".")[0]
        embed = UI.info(
            f"`{Emoji.STATS}` *Bot stats*\n"
            f"> `guilds` *{len(bot.guilds)}*\n"
            f"> `uptime` *{up}*\n"
            f"> `memory` *{mem:.1f} MB*\n"
            f"> `cpu` *{cpu:.1f}%*\n"
            f"> `latency` *{round(bot.latency * 1000)}ms*"
        )
        await ctx.send(embed=embed)

    @sudo_group.command(name="ban_guild")
    @is_sudo()
    async def sudo_ban_guild(ctx: PushieContext, guild_id: int) -> None:
        await bot.storage.ban_guild(guild_id)
        guild = bot.get_guild(guild_id)
        if guild:
            await guild.leave()
        await ctx.ok(f"`{Emoji.BLACKLIST}` *Guild `{guild_id}` banned.*")

    @sudo_group.command(name="unban_guild")
    @is_sudo()
    async def sudo_unban_guild(ctx: PushieContext, guild_id: int) -> None:
        await bot.storage.unban_guild(guild_id)
        await ctx.ok(f"`{Emoji.WHITELIST}` *Guild `{guild_id}` unbanned.*")

    @sudo_group.command(name="ban_user")
    @is_sudo()
    async def sudo_ban_user(ctx: PushieContext, user: discord.User) -> None:
        await bot.storage.ban_user(user.id)
        await ctx.ok(f"`{Emoji.BLACKLIST}` *User {user.mention} banned from bot.*")

    @sudo_group.command(name="unban_user")
    @is_sudo()
    async def sudo_unban_user(ctx: PushieContext, user: discord.User) -> None:
        await bot.storage.unban_user(user.id)
        await ctx.ok(f"`{Emoji.WHITELIST}` *User {user.mention} unbanned from bot.*")

    @sudo_group.command(name="add_sudo")
    @is_sudo()
    async def sudo_add(ctx: PushieContext, user: discord.User) -> None:
        await bot.storage.add_sudo(user.id)
        await ctx.ok(f"`{Emoji.SUDO}` *{user.mention} added to sudo.*")

    @sudo_group.command(name="remove_sudo")
    @is_sudo()
    async def sudo_remove(ctx: PushieContext, user: discord.User) -> None:
        await bot.storage.remove_sudo(user.id)
        await ctx.ok(f"`{Emoji.SUDO}` *{user.mention} removed from sudo.*")

    @sudo_group.command(name="shutdown")
    @is_sudo()
    async def sudo_shutdown(ctx: PushieContext) -> None:
        await ctx.ok(f"`{Emoji.RESTART}` *Shutting down...*")
        await bot.close()


def main() -> None:
    load_dotenv()
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    bot = Pushie()
    _setup_checks(bot)
    _setup_commands(bot)
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
