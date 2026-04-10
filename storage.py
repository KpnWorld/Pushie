from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field, asdict
from typing import Any

from supabase_client import get_client

log = logging.getLogger(__name__)

# Table names in Supabase
GUILD_DATA_TABLE = "guild_data"
GLOBAL_DATA_TABLE = "global_data"


@dataclass
class GuildData:
    id: int = 0
    prefix: str = "!"

    # Logging (general)
    log_channel: int | None = None
    log_events: list[str] = field(default_factory=list)
    log_color: int = 0xFAB9EC
    log_mod_ticket: bool = False
    log_reports_channel: int | None = None

    # Per-type log channels
    member_channel: int | None = None
    mod_channel: int | None = None
    role_channel: int | None = None
    channel_channel: int | None = None
    voice_channel: int | None = None

    # Jail/Blacklist
    jail_channel: int | None = None
    jail_role: int | None = None
    jailed: list[int] = field(default_factory=list)
    user_blacklist: list[int] = field(default_factory=list)
    user_whitelist: list[int] = field(default_factory=list)

    # Welcome/Gate
    welcome_channel: int | None = None
    welcome_role: int | None = None
    welcome_role_bot: int | None = None
    welcome_msg: str | None = None

    greet_enabled: bool = False
    greet_channel: int | None = None
    greet_msg: str | None = None

    leave_enabled: bool = False
    leave_channel: int | None = None
    leave_msg: str | None = None

    ping_enabled: bool = False
    ping_assignments: dict[str, dict[str, Any]] = field(default_factory=dict)

    # Bot Protection
    bot_lock: bool = False
    bot_whitelist: list[int] = field(default_factory=list)
    bot_blacklist: list[int] = field(default_factory=list)

    # Mute Roles
    mute_role: int | None = None
    imute_role: int | None = None
    rmute_role: int | None = None

    # Lockdown
    lockdown_active: bool = False
    lockdown_staff_role: int | None = None

    # Forced Nicks
    forced_nicks: dict[str, str] = field(default_factory=dict)

    # Roles Assignment
    reaction_roles: dict[str, Any] = field(default_factory=dict)
    button_roles: dict[str, Any] = field(default_factory=dict)
    autoroles: list[int] = field(default_factory=list)
    autoroles_human: list[int] = field(default_factory=list)
    autoroles_bot: list[int] = field(default_factory=list)

    # Saved Colors (guild color palette)
    saved_colors: dict[str, str] = field(default_factory=dict)

    # Booster Roles
    booster_setup_enabled: bool = False
    booster_base_role: int | None = None
    booster_base_position: str = "below"
    booster_limit: int = 5
    booster_filters: list[str] = field(default_factory=list)
    booster_shares_limit: int = 3
    booster_hoist: bool = True
    booster_roles: dict[str, dict[str, Any]] = field(default_factory=dict)

    # Friend Groups
    fg_setup_enabled: bool = False
    fg_list: dict[str, dict[str, Any]] = field(default_factory=dict)
    fg_base_role: int | None = None
    fg_base_position: str = "below"
    fg_limit: int = 5
    fg_filters: list[str] = field(default_factory=list)
    fg_manager_role: int | None = None
    fg_vc_bindings: dict[str, int] = field(default_factory=dict)
    fg_role_bindings: dict[str, int] = field(default_factory=dict)

    # Ticket System
    ticket_enabled: bool = False
    ticket_channel: int | None = None
    ticket_panel_msg_id: int | None = None
    ticket_panel_title: str = "Support Ticket"
    ticket_panel_desc: str = "Click the button below to open a ticket."
    ticket_button_label: str = "Open Ticket"
    ticket_report_enabled: bool = False
    ticket_reports_channel: int | None = None
    ticket_managers: list[int] = field(default_factory=list)
    tickets: dict[str, dict[str, Any]] = field(default_factory=dict)
    transcripts: dict[str, dict[str, Any]] = field(default_factory=dict)

    # Levels
    levels_enabled: bool = False
    levels_channel: int | None = None
    levels_msg: str | None = None
    levels_xp_leaderboard: dict[str, int] = field(default_factory=dict)
    levels_list: list[dict[str, Any]] = field(default_factory=list)

    # User AFK
    afks: dict[str, Any] = field(default_factory=dict)

    # Sticky Messages
    sticky_messages: dict[str, Any] = field(default_factory=dict)

    # Autoresponders
    autoresponders: dict[str, Any] = field(default_factory=dict)

    # Embed Templates
    embed_templates: dict[str, Any] = field(default_factory=dict)

    # Warnings & Moderation
    warnings: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    warn_strikes: dict[str, dict[str, Any]] = field(default_factory=dict)

    # Invoke Messages (mod action messages)
    invoke_messages: dict[str, dict[str, str]] = field(default_factory=dict)

    # Security / Automod filters
    keyword_filters: list[str] = field(default_factory=list)
    link_filters: list[str] = field(default_factory=list)
    invite_filters: list[str] = field(default_factory=list)
    regex_filters: list[str] = field(default_factory=list)
    filter_whitelist: list[str] = field(default_factory=list)
    filter_link_whitelist: list[str] = field(default_factory=list)
    filter_exempts: list[int] = field(default_factory=list)
    nickname_filters: list[str] = field(default_factory=list)
    filter_snipe: bool = False
    fake_permissions: dict[str, list[str]] = field(default_factory=dict)

    # Antinuke
    antinuke_enabled: bool = False
    antinuke_whitelist: list[int] = field(default_factory=list)
    antinuke_admins: list[int] = field(default_factory=list)
    antinuke_kick: bool = False
    antinuke_ban: bool = False
    antinuke_vanity: bool = False
    antinuke_guildupdate: bool = False
    antinuke_botadd: bool = False

    # Antiraid
    antiraid_enabled: bool = False
    antiraid_username_patterns: list[str] = field(default_factory=list)
    antiraid_whitelist: list[int] = field(default_factory=list)
    antiraid_massmention: bool = False
    antiraid_massjoin: bool = False
    antiraid_age: bool = False
    antiraid_avatar: bool = False
    antiraid_unverifiedbots: bool = False

    # Voice Centre
    voicecenter_channel: int | None = None
    voicecenter_category: int | None = None
    voicecenter_interface: int | None = None
    voicecenter_mode: str = "temp"
    voicecenter_defaults: dict[str, Any] = field(default_factory=dict)
    voicecenter_rolejoin: int | None = None
    voicecenter_temp_channels: dict[str, dict[str, Any]] = field(default_factory=dict)
    voicecenter_allowance: bool = False
    voicecenter_allowed: list[int] = field(default_factory=list)
    voicecenter_disallowed: list[int] = field(default_factory=list)
    voicecenter_systems: list[dict[str, Any]] = field(default_factory=list)

    # Timers (scheduled messages)
    timers: dict[str, dict[str, Any]] = field(default_factory=dict)

    # Counters
    counters: dict[str, dict[str, Any]] = field(default_factory=dict)

    # Reminders
    reminders: dict[str, dict[str, Any]] = field(default_factory=dict)
    bump_reminder_msg: str | None = None
    bump_thankyou_msg: str | None = None
    bump_autolock: bool = False

    # Role Backup
    role_backup: dict[str, list[int]] = field(default_factory=dict)

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
    default_presence: dict[str, Any] = field(default_factory=dict)

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
        self._client: Any = None

    async def _get_client(self) -> Any:
        """Get Supabase client."""
        if self._client is None:
            self._client = await get_client()
        return self._client

    async def load_all(self) -> None:
        """Load all guild and global data from Supabase."""
        await self._load_global()
        client = await self._get_client()

        # Load all guilds from Supabase
        try:
            response = await client.table(GUILD_DATA_TABLE).select("*").execute()
            for row in response.data:
                try:
                    guild_id = row["id"]
                    guild_json = row["data"]
                    g = GuildData.from_dict(guild_json)
                    self._guild_cache[guild_id] = g
                except Exception as e:
                    log.warning("Failed to load guild %s: %s", row.get("id"), e)
        except Exception as e:
            log.error("Failed to load guilds from Supabase: %s", e)

        log.info("Storage loaded: %d guild(s)", len(self._guild_cache))

    async def _load_global(self) -> None:
        """Load global data from Supabase."""
        client = await self._get_client()
        try:
            response = (
                await client.table(GLOBAL_DATA_TABLE)
                .select("data")
                .eq("id", 1)
                .execute()
            )
            if response.data and len(response.data) > 0:
                self.global_data = GlobalData.from_dict(response.data[0]["data"])
            else:
                self.global_data = GlobalData()
                await self.save_global()
        except Exception as e:
            log.error("Failed to load global.json: %s", e)
            self.global_data = GlobalData()

    async def save_global(self) -> None:
        """Save global data to Supabase."""
        async with self._global_lock:
            client = await self._get_client()
            try:
                # Try to update, if not exists, insert
                response = (
                    await client.table(GLOBAL_DATA_TABLE)
                    .select("id")
                    .eq("id", 1)
                    .execute()
                )
                if response.data:
                    await client.table(GLOBAL_DATA_TABLE).update(
                        {"data": self.global_data.to_dict()}
                    ).eq("id", 1).execute()
                else:
                    await client.table(GLOBAL_DATA_TABLE).insert(
                        {"id": 1, "data": self.global_data.to_dict()}
                    ).execute()
            except Exception as e:
                log.error("Failed to save global data: %s", e)

    def _get_lock(self, guild_id: int) -> asyncio.Lock:
        if guild_id not in self._guild_locks:
            self._guild_locks[guild_id] = asyncio.Lock()
        return self._guild_locks[guild_id]

    async def get_guild(self, guild_id: int) -> GuildData:
        """Get guild data, loading from Supabase if not cached."""
        if guild_id in self._guild_cache:
            return self._guild_cache[guild_id]

        client = await self._get_client()
        try:
            response = (
                await client.table(GUILD_DATA_TABLE)
                .select("data")
                .eq("id", guild_id)
                .execute()
            )
            if response.data and len(response.data) > 0:
                g = GuildData.from_dict(response.data[0]["data"])
            else:
                g = GuildData(id=guild_id)
                await self.save_guild(g)
        except Exception as e:
            log.error("Failed to load guild %s: %s", guild_id, e)
            g = GuildData(id=guild_id)

        self._guild_cache[guild_id] = g
        return g

    async def save_guild(self, guild: GuildData) -> None:
        """Save guild data to Supabase."""
        self._guild_cache[guild.id] = guild
        async with self._get_lock(guild.id):
            client = await self._get_client()
            try:
                response = (
                    await client.table(GUILD_DATA_TABLE)
                    .select("id")
                    .eq("id", guild.id)
                    .execute()
                )
                if response.data:
                    await client.table(GUILD_DATA_TABLE).update(
                        {"data": guild.to_dict()}
                    ).eq("id", guild.id).execute()
                else:
                    await client.table(GUILD_DATA_TABLE).insert(
                        {"id": guild.id, "data": guild.to_dict()}
                    ).execute()
            except Exception as e:
                log.error("Failed to save guild %s: %s", guild.id, e)

    def get_guild_sync(self, guild_id: int) -> GuildData | None:
        """Get cached guild data synchronously."""
        return self._guild_cache.get(guild_id)

    async def delete_guild(self, guild_id: int) -> None:
        """Delete guild data from Supabase."""
        self._guild_cache.pop(guild_id, None)
        self._guild_locks.pop(guild_id, None)
        client = await self._get_client()
        try:
            await client.table(GUILD_DATA_TABLE).delete().eq("id", guild_id).execute()
        except Exception as e:
            log.error("Failed to delete guild %s: %s", guild_id, e)

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
        g.voicecenter_interface = None
        g.voicecenter_defaults.clear()
        g.voicecenter_rolejoin = None
        g.voicecenter_temp_channels.clear()
        g.voicecenter_allowance = False
        g.voicecenter_allowed.clear()
        g.voicecenter_disallowed.clear()
        g.voicecenter_systems.clear()
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
        g = await self.get_guild(guild_id)
        for key, value in kwargs.items():
            if hasattr(g, key):
                setattr(g, key, value)
        await self.save_guild(g)

    # Ticket System Methods
    async def set_ticket_channel(self, guild_id: int, channel_id: int) -> None:
        g = await self.get_guild(guild_id)
        g.ticket_channel = channel_id
        await self.save_guild(g)

    async def add_ticket_manager(self, guild_id: int, user_id: int) -> None:
        g = await self.get_guild(guild_id)
        if user_id not in g.ticket_managers:
            g.ticket_managers.append(user_id)
            await self.save_guild(g)

    async def remove_ticket_manager(self, guild_id: int, user_id: int) -> None:
        g = await self.get_guild(guild_id)
        if user_id in g.ticket_managers:
            g.ticket_managers.remove(user_id)
            await self.save_guild(g)

    # Autorole Methods
    async def add_autorole(
        self, guild_id: int, role_id: int, target: str = "all"
    ) -> None:
        g = await self.get_guild(guild_id)
        if target == "human":
            if role_id not in g.autoroles_human:
                g.autoroles_human.append(role_id)
        elif target == "bot":
            if role_id not in g.autoroles_bot:
                g.autoroles_bot.append(role_id)
        else:
            if role_id not in g.autoroles:
                g.autoroles.append(role_id)
        await self.save_guild(g)

    async def remove_autorole(
        self, guild_id: int, role_id: int, target: str = "all"
    ) -> None:
        g = await self.get_guild(guild_id)
        if target == "human":
            if role_id in g.autoroles_human:
                g.autoroles_human.remove(role_id)
        elif target == "bot":
            if role_id in g.autoroles_bot:
                g.autoroles_bot.remove(role_id)
        else:
            if role_id in g.autoroles:
                g.autoroles.remove(role_id)
        await self.save_guild(g)

    # Button Roles Methods
    async def add_button_role(self, guild_id: int, key: str, role_id: int) -> None:
        g = await self.get_guild(guild_id)
        g.button_roles[key] = role_id
        await self.save_guild(g)

    async def remove_button_role(self, guild_id: int, key: str) -> None:
        g = await self.get_guild(guild_id)
        g.button_roles.pop(key, None)
        await self.save_guild(g)

    # Booster Role Methods
    async def add_booster_role(
        self, guild_id: int, user_id: int, role_info: dict[str, Any]
    ) -> None:
        g = await self.get_guild(guild_id)
        g.booster_roles[str(user_id)] = role_info
        await self.save_guild(g)

    async def remove_booster_role(self, guild_id: int, user_id: int) -> None:
        g = await self.get_guild(guild_id)
        g.booster_roles.pop(str(user_id), None)
        await self.save_guild(g)

    # Friend Group Methods
    async def add_friend_group(
        self, guild_id: int, name: str, group_info: dict[str, Any]
    ) -> None:
        g = await self.get_guild(guild_id)
        g.fg_list[name] = group_info
        await self.save_guild(g)

    async def remove_friend_group(self, guild_id: int, name: str) -> None:
        g = await self.get_guild(guild_id)
        g.fg_list.pop(name, None)
        await self.save_guild(g)

    # Greet/Leave Methods
    async def set_greet_config(self, guild_id: int, channel_id: int, msg: str) -> None:
        g = await self.get_guild(guild_id)
        g.greet_channel = channel_id
        g.greet_msg = msg
        g.greet_enabled = True
        await self.save_guild(g)

    async def set_leave_config(self, guild_id: int, channel_id: int, msg: str) -> None:
        g = await self.get_guild(guild_id)
        g.leave_channel = channel_id
        g.leave_msg = msg
        g.leave_enabled = True
        await self.save_guild(g)

    # Ping on Join Methods
    async def add_ping_assignment(
        self, guild_id: int, channel_id: int, config: dict[str, Any]
    ) -> None:
        g = await self.get_guild(guild_id)
        g.ping_assignments[str(channel_id)] = config
        await self.save_guild(g)

    async def remove_ping_assignment(self, guild_id: int, channel_id: int) -> None:
        g = await self.get_guild(guild_id)
        g.ping_assignments.pop(str(channel_id), None)
        await self.save_guild(g)

    # Level Methods
    async def add_level(self, guild_id: int, level: int, role_id: int) -> None:
        g = await self.get_guild(guild_id)
        g.levels_list.append({"level": level, "role_id": role_id})
        await self.save_guild(g)

    async def remove_level(self, guild_id: int, level: int) -> None:
        g = await self.get_guild(guild_id)
        g.levels_list = [l for l in g.levels_list if l.get("level") != level]
        await self.save_guild(g)

    async def add_xp(self, guild_id: int, user_id: int, amount: int) -> None:
        g = await self.get_guild(guild_id)
        current = g.levels_xp_leaderboard.get(str(user_id), 0)
        g.levels_xp_leaderboard[str(user_id)] = current + amount
        await self.save_guild(g)

    def get_user_xp(self, g: GuildData, user_id: int) -> int:
        return g.levels_xp_leaderboard.get(str(user_id), 0)

    def xp_to_level(self, xp: int) -> int:
        level = 0
        while xp >= self.level_to_xp(level + 1):
            level += 1
        return level

    def level_to_xp(self, level: int) -> int:
        return 5 * (level**2) + 50 * level + 100

    # Timer Methods
    async def add_timer(
        self, guild_id: int, timer_id: str, config: dict[str, Any]
    ) -> None:
        g = await self.get_guild(guild_id)
        g.timers[timer_id] = config
        await self.save_guild(g)

    async def remove_timer(self, guild_id: int, timer_id: str) -> None:
        g = await self.get_guild(guild_id)
        g.timers.pop(timer_id, None)
        await self.save_guild(g)

    # Counter Methods
    async def add_counter(self, guild_id: int, channel_id: int) -> None:
        g = await self.get_guild(guild_id)
        g.counters[str(channel_id)] = {"count": 0, "paused": False}
        await self.save_guild(g)

    async def remove_counter(self, guild_id: int, channel_id: int) -> None:
        g = await self.get_guild(guild_id)
        g.counters.pop(str(channel_id), None)
        await self.save_guild(g)

    # Reminder Methods
    async def add_reminder(
        self, guild_id: int, reminder_id: str, config: dict[str, Any]
    ) -> None:
        g = await self.get_guild(guild_id)
        g.reminders[reminder_id] = config
        await self.save_guild(g)

    async def remove_reminder(self, guild_id: int, reminder_id: str) -> None:
        g = await self.get_guild(guild_id)
        g.reminders.pop(reminder_id, None)
        await self.save_guild(g)

    # Warning Methods
    async def add_warning(
        self, guild_id: int, user_id: int, warning_info: dict[str, Any]
    ) -> None:
        g = await self.get_guild(guild_id)
        key = str(user_id)
        if key not in g.warnings:
            g.warnings[key] = []
        g.warnings[key].append(warning_info)
        await self.save_guild(g)

    async def clear_warnings(self, guild_id: int, user_id: int) -> None:
        g = await self.get_guild(guild_id)
        g.warnings.pop(str(user_id), None)
        await self.save_guild(g)
