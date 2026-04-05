from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

DATA_DIR = Path("data")
GUILDS_DIR = DATA_DIR / "guilds"
GLOBAL_FILE = DATA_DIR / "global.json"


@dataclass
class GuildData:
    id: int = 0
    prefix: str = "!"

    log_channel: int | None = None
    log_events: list[str] = field(default_factory=list)

    jail_channel: int | None = None
    jail_role: int | None = None
    jailed: list[int] = field(default_factory=list)
    user_blacklist: list[int] = field(default_factory=list)
    user_whitelist: list[int] = field(default_factory=list)

    welcome_channel: int | None = None
    welcome_role: int | None = None
    welcome_role_bot: int | None = None
    welcome_msg: str | None = None

    bot_lock: bool = False
    bot_whitelist: list[int] = field(default_factory=list)
    bot_blacklist: list[int] = field(default_factory=list)

    mute_role: int | None = None
    imute_role: int | None = None
    rmute_role: int | None = None

    reaction_roles: dict[str, int] = field(
        default_factory=dict
    )
    booster_roles: list[int] = field(default_factory=list)

    afks: dict[str, Any] = field(default_factory=dict)

    sticky_messages: dict[str, Any] = field(default_factory=dict)

    autoresponders: dict[str, Any] = field(default_factory=dict)

    embed_templates: dict[str, Any] = field(default_factory=dict)

    warnings: dict[str, list[dict[str, Any]]] = field(default_factory=dict)

    voicecenter_channel: int | None = None
    voicecenter_category: int | None = None
    voicecenter_defaults: dict[str, Any] = field(default_factory=dict)
    voicecenter_rolejoin: int | None = None
    voicecenter_temp_channels: dict[int, dict[str, Any]] = field(default_factory=dict)

    role_backup: dict[int, dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "GuildData":
        valid = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in valid})


@dataclass
class GlobalData:
    sudo_users: list[int] = field(default_factory=list)
    banned_guilds: list[int] = field(default_factory=list)
    banned_users: list[int] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "GlobalData":
        valid = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in valid})


class StorageManager:

    def __init__(self) -> None:
        self._guild_cache: dict[int, GuildData] = {}
        self._guild_locks: dict[int, asyncio.Lock] = {}
        self._global_lock = asyncio.Lock()
        self.global_data: GlobalData = GlobalData()
        GUILDS_DIR.mkdir(parents=True, exist_ok=True)

    async def load_all(self) -> None:
        await self._load_global()
        for path in GUILDS_DIR.glob("*.json"):
            try:
                await self.get_guild(int(path.stem))
            except Exception as e:
                log.warning("Failed to load guild file %s: %s", path, e)
        log.info("Storage loaded: %d guild(s)", len(self._guild_cache))

    async def _load_global(self) -> None:
        if GLOBAL_FILE.exists():
            try:
                self.global_data = GlobalData.from_dict(
                    json.loads(GLOBAL_FILE.read_text("utf-8"))
                )
            except Exception as e:
                log.error("Failed to load global.json: %s", e)
                self.global_data = GlobalData()
        else:
            self.global_data = GlobalData()
            await self.save_global()

    async def save_global(self) -> None:
        async with self._global_lock:
            await asyncio.to_thread(
                GLOBAL_FILE.write_text,
                json.dumps(self.global_data.to_dict(), indent=2),
                "utf-8",
            )

    def _guild_path(self, guild_id: int) -> Path:
        return GUILDS_DIR / f"{guild_id}.json"

    def _get_lock(self, guild_id: int) -> asyncio.Lock:
        if guild_id not in self._guild_locks:
            self._guild_locks[guild_id] = asyncio.Lock()
        return self._guild_locks[guild_id]

    async def get_guild(self, guild_id: int) -> GuildData:
        if guild_id in self._guild_cache:
            return self._guild_cache[guild_id]
        path = self._guild_path(guild_id)
        if path.exists():
            try:
                g = GuildData.from_dict(json.loads(path.read_text("utf-8")))
            except Exception as e:
                log.error("Corrupt guild file %s: %s — using defaults", path, e)
                g = GuildData(id=guild_id)
        else:
            g = GuildData(id=guild_id)
            await self.save_guild(g)
        self._guild_cache[guild_id] = g
        return g

    async def save_guild(self, guild: GuildData) -> None:
        self._guild_cache[guild.id] = guild
        async with self._get_lock(guild.id):
            await asyncio.to_thread(
                self._guild_path(guild.id).write_text,
                json.dumps(guild.to_dict(), indent=2),
                "utf-8",
            )

    def get_guild_sync(self, guild_id: int) -> GuildData | None:
        return self._guild_cache.get(guild_id)

    async def delete_guild(self, guild_id: int) -> None:
        self._guild_cache.pop(guild_id, None)
        self._guild_locks.pop(guild_id, None)
        path = self._guild_path(guild_id)
        if path.exists():
            await asyncio.to_thread(path.unlink)

    async def set_prefix(self, guild_id: int, prefix: str) -> None:
        g = await self.get_guild(guild_id)
        g.prefix = prefix
        await self.save_guild(g)

    async def set_afk(
        self, guild_id: int, user_id: int, reason: str, since: float
    ) -> None:
        g = await self.get_guild(guild_id)
        g.afks[str(user_id)] = {"reason": reason, "since": since}
        await self.save_guild(g)

    async def clear_afk(self, guild_id: int, user_id: int) -> None:
        g = await self.get_guild(guild_id)
        g.afks.pop(str(user_id), None)
        await self.save_guild(g)

    async def add_reaction_role(self, guild_id: int, key: str, role_id: int) -> None:
        g = await self.get_guild(guild_id)
        g.reaction_roles[key] = role_id
        await self.save_guild(g)

    async def remove_reaction_role(self, guild_id: int, key: str) -> None:
        g = await self.get_guild(guild_id)
        g.reaction_roles.pop(key, None)
        await self.save_guild(g)

    async def set_voicecenter_channel(self, guild_id: int, channel_id: int) -> None:
        g = await self.get_guild(guild_id)
        g.voicecenter_channel = channel_id
        await self.save_guild(g)

    async def set_voicecenter_category(self, guild_id: int, category_id: int) -> None:
        g = await self.get_guild(guild_id)
        g.voicecenter_category = category_id
        await self.save_guild(g)

    async def set_voicecenter_default(
        self, guild_id: int, key: str, value: Any
    ) -> None:
        g = await self.get_guild(guild_id)
        if not g.voicecenter_defaults:
            g.voicecenter_defaults = {}
        g.voicecenter_defaults[key] = value
        await self.save_guild(g)

    async def set_voicecenter_rolejoin(self, guild_id: int, role_id: int) -> None:
        g = await self.get_guild(guild_id)
        g.voicecenter_rolejoin = role_id
        await self.save_guild(g)

    async def clear_voicecenter(self, guild_id: int) -> None:
        g = await self.get_guild(guild_id)
        g.voicecenter_channel = None
        g.voicecenter_category = None
        g.voicecenter_defaults.clear()
        g.voicecenter_rolejoin = None
        g.voicecenter_temp_channels.clear()
        await self.save_guild(g)

    def is_sudo(self, user_id: int) -> bool:
        return user_id in self.global_data.sudo_users

    def is_banned_guild(self, guild_id: int) -> bool:
        return guild_id in self.global_data.banned_guilds

    def is_banned_user(self, user_id: int) -> bool:
        return user_id in self.global_data.banned_users

    async def add_sudo(self, user_id: int) -> None:
        if user_id not in self.global_data.sudo_users:
            self.global_data.sudo_users.append(user_id)
            await self.save_global()

    async def remove_sudo(self, user_id: int) -> None:
        if user_id in self.global_data.sudo_users:
            self.global_data.sudo_users.remove(user_id)
            await self.save_global()

    async def ban_guild(self, guild_id: int) -> None:
        if guild_id not in self.global_data.banned_guilds:
            self.global_data.banned_guilds.append(guild_id)
            await self.save_global()

    async def unban_guild(self, guild_id: int) -> None:
        if guild_id in self.global_data.banned_guilds:
            self.global_data.banned_guilds.remove(guild_id)
            await self.save_global()

    async def ban_user(self, user_id: int) -> None:
        if user_id not in self.global_data.banned_users:
            self.global_data.banned_users.append(user_id)
            await self.save_global()

    async def unban_user(self, user_id: int) -> None:
        if user_id in self.global_data.banned_users:
            self.global_data.banned_users.remove(user_id)
            await self.save_global()

    async def update_setup(self, guild_id: int, **kwargs: Any) -> None:
        """Bulk-update any GuildData fields by keyword and save once."""
        g = await self.get_guild(guild_id)
        for key, value in kwargs.items():
            if hasattr(g, key):
                setattr(g, key, value)
        await self.save_guild(g)
