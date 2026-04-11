from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any

from dbclient import get_client

log = logging.getLogger(__name__)


@dataclass
class GuildData:
    id: int = 0
    prefix: str = ","

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

    # Staff / Base roles
    staff_roles: list[int] = field(default_factory=list)
    base_role: int | None = None
    autonick: str | None = None
    modlog_channel: int | None = None

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
    booster_limit: int = 1
    booster_filters: list[str] = field(default_factory=list)
    booster_shares_limit: int = 5
    booster_shares_max: int = 3
    booster_hoist: bool = True
    booster_roles: dict[str, dict[str, Any]] = field(default_factory=dict)
    booster_award_role: int | None = None

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
    ticket_support_role: int | None = None
    ticket_log_channel: int | None = None
    ticket_welcome_message: str | None = None
    ticket_category: int | None = None

    # Levels
    levels_enabled: bool = True
    levels_channel: int | None = None
    levels_msg: str | None = None
    levels_xp_leaderboard: dict[str, int] = field(default_factory=dict)
    levels_list: list[dict[str, Any]] = field(default_factory=list)
    levels_xp_multiplier: float = 1.0
    levels_message_mode: str = "channel"
    levels_stack_roles: bool = False

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
    voicecenter_private_category: int | None = None
    voicecenter_interface: int | None = None
    voicecenter_mode: str = "temp"
    voicecenter_defaults: dict[str, Any] = field(default_factory=dict)
    voicecenter_rolejoin: int | None = None
    voicecenter_temp_channels: dict[str, dict[str, Any]] = field(default_factory=dict)
    voicecenter_allowance: bool = False
    voicecenter_allowed: list[int] = field(default_factory=list)
    voicecenter_disallowed: list[int] = field(default_factory=list)
    voicecenter_systems: list[dict[str, Any]] = field(default_factory=list)
    voicecenter_send_interface: bool = True
    voicecenter_default_name: str = "{username} channel"
    voicecenter_default_bitrate: int = 64000
    voicecenter_default_region: str | None = None

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


def _map_guild_config_row(g: GuildData, row: dict) -> None:
    """Map a guild_config row into a GuildData object."""
    g.prefix = row.get("prefix") or ","
    g.bot_lock = row.get("bot_lock") or False
    g.mute_role = row.get("muted_role")
    g.imute_role = row.get("imuted_role")
    g.rmute_role = row.get("rmuted_role")
    g.jail_channel = row.get("jail_channel")
    g.greet_enabled = row.get("greet_enabled") or False
    g.greet_channel = row.get("greet_channel")
    g.greet_msg = row.get("greet_msg")
    g.leave_enabled = row.get("leave_enabled") or False
    g.leave_channel = row.get("leave_channel")
    g.leave_msg = row.get("leave_msg")
    g.ping_enabled = row.get("ping_enabled") or False
    g.lockdown_staff_role = row.get("lockdown_staff_role")
    g.member_channel = row.get("member_log_channel")
    g.mod_channel = row.get("mod_log_channel")
    g.role_channel = row.get("role_log_channel")
    g.channel_channel = row.get("channel_log_channel")
    g.voice_channel = row.get("voice_log_channel")
    g.log_channel = row.get("general_log_channel")
    g.log_color = row.get("log_color") or 0xFAB9EC
    g.modlog_channel = row.get("modlog_channel")
    g.base_role = row.get("base_role")
    g.autonick = row.get("autonick")
    staff = row.get("staff_roles")
    if staff:
        g.staff_roles = [int(r) for r in staff]


class StorageManager:

    def __init__(self) -> None:
        self._guild_cache: dict[int, GuildData] = {}
        self._guild_locks: dict[int, asyncio.Lock] = {}
        self.global_data: GlobalData = GlobalData()

    def _get_lock(self, guild_id: int) -> asyncio.Lock:
        if guild_id not in self._guild_locks:
            self._guild_locks[guild_id] = asyncio.Lock()
        return self._guild_locks[guild_id]

    # ── STARTUP ────────────────────────────────────────────────────────────

    async def load_all(self) -> None:
        """Load all guild and global data from Supabase."""
        client = await get_client()

        # Load sudo users
        try:
            res = await client.table("sudo_users").select("user_id").execute()
            self.global_data.sudo_users = [int(r["user_id"]) for r in (res.data or [])]
        except Exception as e:
            log.error("Failed to load sudo_users: %s", e)

        # Load banned guilds and users from guild_blacklist
        try:
            res = (
                await client.table("guild_blacklist")
                .select("target_id, scope")
                .execute()
            )
            self.global_data.banned_guilds = [
                int(r["target_id"]) for r in (res.data or []) if r["scope"] == "guild"
            ]
            self.global_data.banned_users = [
                int(r["target_id"]) for r in (res.data or []) if r["scope"] == "user"
            ]
        except Exception as e:
            log.error("Failed to load guild_blacklist: %s", e)

        # Load guild_config
        try:
            res = await client.table("guild_config").select("*").execute()
            for row in res.data or []:
                gid = int(row["guild_id"])
                if gid not in self._guild_cache:
                    self._guild_cache[gid] = GuildData(id=gid)
                _map_guild_config_row(self._guild_cache[gid], row)
        except Exception as e:
            log.error("Failed to load guild_config: %s", e)

        # Load AFK data into guild caches
        try:
            res = await client.table("afk").select("*").execute()
            for row in res.data or []:
                gid = int(row["guild_id"])
                uid = int(row["user_id"])
                if gid not in self._guild_cache:
                    self._guild_cache[gid] = GuildData(id=gid)
                set_at = row.get("set_at")
                since = (
                    datetime.fromisoformat(set_at).timestamp()
                    if set_at
                    else 0.0
                )
                self._guild_cache[gid].afks[str(uid)] = {
                    "reason": row.get("status") or "",
                    "since": since,
                }
        except Exception as e:
            log.error("Failed to load afk: %s", e)

        # Load antinuke config
        try:
            res = await client.table("antinuke_config").select("*").execute()
            for row in res.data or []:
                gid = int(row["guild_id"])
                if gid not in self._guild_cache:
                    self._guild_cache[gid] = GuildData(id=gid)
                g = self._guild_cache[gid]
                g.antinuke_enabled = row.get("enabled") or False
                g.antinuke_kick = row.get("kick_protection") or False
                g.antinuke_ban = row.get("ban_protection") or False
                g.antinuke_vanity = row.get("vanity_protection") or False
                g.antinuke_guildupdate = row.get("guild_update") or False
                g.antinuke_botadd = row.get("bot_add") or False
        except Exception as e:
            log.error("Failed to load antinuke_config: %s", e)

        # Load antinuke whitelist
        try:
            res = await client.table("antinuke_whitelist").select("guild_id, user_id").execute()
            for row in res.data or []:
                gid = int(row["guild_id"])
                if gid not in self._guild_cache:
                    self._guild_cache[gid] = GuildData(id=gid)
                uid = int(row["user_id"])
                if uid not in self._guild_cache[gid].antinuke_whitelist:
                    self._guild_cache[gid].antinuke_whitelist.append(uid)
        except Exception as e:
            log.error("Failed to load antinuke_whitelist: %s", e)

        # Load antinuke admins
        try:
            res = await client.table("antinuke_admins").select("guild_id, user_id").execute()
            for row in res.data or []:
                gid = int(row["guild_id"])
                if gid not in self._guild_cache:
                    self._guild_cache[gid] = GuildData(id=gid)
                uid = int(row["user_id"])
                if uid not in self._guild_cache[gid].antinuke_admins:
                    self._guild_cache[gid].antinuke_admins.append(uid)
        except Exception as e:
            log.error("Failed to load antinuke_admins: %s", e)

        # Load antiraid config
        try:
            res = await client.table("antiraid_config").select("*").execute()
            for row in res.data or []:
                gid = int(row["guild_id"])
                if gid not in self._guild_cache:
                    self._guild_cache[gid] = GuildData(id=gid)
                g = self._guild_cache[gid]
                g.antiraid_enabled = row.get("enabled") or False
                g.antiraid_massmention = row.get("massmention") or False
                g.antiraid_massjoin = row.get("massjoin") or False
                g.antiraid_age = row.get("age_protection") or False
                g.antiraid_avatar = row.get("avatar_protection") or False
                g.antiraid_unverifiedbots = row.get("unverified_bots") or False
        except Exception as e:
            log.error("Failed to load antiraid_config: %s", e)

        # Load antiraid whitelist
        try:
            res = await client.table("antiraid_whitelist").select("guild_id, user_id").execute()
            for row in res.data or []:
                gid = int(row["guild_id"])
                if gid not in self._guild_cache:
                    self._guild_cache[gid] = GuildData(id=gid)
                uid = int(row["user_id"])
                if uid not in self._guild_cache[gid].antiraid_whitelist:
                    self._guild_cache[gid].antiraid_whitelist.append(uid)
        except Exception as e:
            log.error("Failed to load antiraid_whitelist: %s", e)

        # Load antiraid username patterns
        try:
            res = await client.table("antiraid_username_patterns").select("guild_id, pattern").execute()
            for row in res.data or []:
                gid = int(row["guild_id"])
                if gid not in self._guild_cache:
                    self._guild_cache[gid] = GuildData(id=gid)
                p = row.get("pattern")
                if p and p not in self._guild_cache[gid].antiraid_username_patterns:
                    self._guild_cache[gid].antiraid_username_patterns.append(p)
        except Exception as e:
            log.error("Failed to load antiraid_username_patterns: %s", e)

        # Load autoroles
        try:
            res = await client.table("autoroles").select("guild_id, role_id, target_type").execute()
            for row in res.data or []:
                gid = int(row["guild_id"])
                if gid not in self._guild_cache:
                    self._guild_cache[gid] = GuildData(id=gid)
                g = self._guild_cache[gid]
                rid = int(row["role_id"])
                t = row.get("target_type", "all")
                if t == "human":
                    if rid not in g.autoroles_human:
                        g.autoroles_human.append(rid)
                elif t == "bot":
                    if rid not in g.autoroles_bot:
                        g.autoroles_bot.append(rid)
                else:
                    if rid not in g.autoroles:
                        g.autoroles.append(rid)
        except Exception as e:
            log.error("Failed to load autoroles: %s", e)

        # Load voicecentre config
        try:
            res = await client.table("voicecentre_config").select("*").execute()
            for row in res.data or []:
                gid = int(row["guild_id"])
                if gid not in self._guild_cache:
                    self._guild_cache[gid] = GuildData(id=gid)
                g = self._guild_cache[gid]
                g.voicecenter_allowance = row.get("enabled") or False
                g.voicecenter_channel = row.get("create_channel_id")
                g.voicecenter_category = row.get("category_id")
                g.voicecenter_private_category = row.get("private_category_id")
                g.voicecenter_rolejoin = row.get("join_role_id")
                g.voicecenter_send_interface = row.get("send_interface") if row.get("send_interface") is not None else True
                g.voicecenter_default_name = row.get("default_name") or "{username} channel"
                g.voicecenter_default_bitrate = row.get("default_bitrate") or 64000
                g.voicecenter_default_region = row.get("default_region")
        except Exception as e:
            log.error("Failed to load voicecentre_config: %s", e)

        # Load ticket config
        try:
            res = await client.table("ticket_config").select("*").execute()
            for row in res.data or []:
                gid = int(row["guild_id"])
                if gid not in self._guild_cache:
                    self._guild_cache[gid] = GuildData(id=gid)
                g = self._guild_cache[gid]
                g.ticket_category = row.get("category_id")
                g.ticket_support_role = row.get("support_role_id")
                g.ticket_log_channel = row.get("log_channel_id")
                g.ticket_welcome_message = row.get("welcome_message")
        except Exception as e:
            log.error("Failed to load ticket_config: %s", e)

        # Load ticket managers
        try:
            res = await client.table("ticket_managers").select("guild_id, target_id, target_type").execute()
            for row in res.data or []:
                gid = int(row["guild_id"])
                if gid not in self._guild_cache:
                    self._guild_cache[gid] = GuildData(id=gid)
                if row.get("target_type") == "user":
                    uid = int(row["target_id"])
                    if uid not in self._guild_cache[gid].ticket_managers:
                        self._guild_cache[gid].ticket_managers.append(uid)
        except Exception as e:
            log.error("Failed to load ticket_managers: %s", e)

        # Load booster role config
        try:
            res = await client.table("booster_role_config").select("*").execute()
            for row in res.data or []:
                gid = int(row["guild_id"])
                if gid not in self._guild_cache:
                    self._guild_cache[gid] = GuildData(id=gid)
                g = self._guild_cache[gid]
                g.booster_setup_enabled = row.get("enabled") or False
                g.booster_base_role = row.get("base_role_id")
                g.booster_base_position = row.get("base_position") or "below"
                g.booster_limit = row.get("role_limit") or 1
                g.booster_shares_limit = row.get("share_limit") or 5
                g.booster_shares_max = row.get("share_max") or 3
                g.booster_award_role = row.get("award_role_id")
                g.booster_hoist = row.get("hoist_new") if row.get("hoist_new") is not None else True
                bw = row.get("blacklisted_words")
                if bw:
                    g.booster_filters = list(bw)
        except Exception as e:
            log.error("Failed to load booster_role_config: %s", e)

        # Load booster roles
        try:
            res = await client.table("booster_roles").select("guild_id, user_id, role_id").execute()
            for row in res.data or []:
                gid = int(row["guild_id"])
                if gid not in self._guild_cache:
                    self._guild_cache[gid] = GuildData(id=gid)
                uid = str(row["user_id"])
                rid = int(row["role_id"])
                self._guild_cache[gid].booster_roles[uid] = {"role_id": rid}
        except Exception as e:
            log.error("Failed to load booster_roles: %s", e)

        # Load warn_strikes
        try:
            res = await client.table("warn_strikes").select("guild_id, strike, action").execute()
            for row in res.data or []:
                gid = int(row["guild_id"])
                if gid not in self._guild_cache:
                    self._guild_cache[gid] = GuildData(id=gid)
                self._guild_cache[gid].warn_strikes[str(row["strike"])] = {"action": row["action"]}
        except Exception as e:
            log.error("Failed to load warn_strikes: %s", e)

        # Load fake_permissions
        try:
            res = await client.table("fake_permissions").select("guild_id, role_id, permission").execute()
            for row in res.data or []:
                gid = int(row["guild_id"])
                if gid not in self._guild_cache:
                    self._guild_cache[gid] = GuildData(id=gid)
                g = self._guild_cache[gid]
                key = str(row["role_id"])
                if key not in g.fake_permissions:
                    g.fake_permissions[key] = []
                perm = row.get("permission")
                if perm and perm not in g.fake_permissions[key]:
                    g.fake_permissions[key].append(perm)
        except Exception as e:
            log.error("Failed to load fake_permissions: %s", e)

        # Load forced_nicks
        try:
            res = await client.table("forced_nicks").select("guild_id, user_id, nickname").execute()
            for row in res.data or []:
                gid = int(row["guild_id"])
                if gid not in self._guild_cache:
                    self._guild_cache[gid] = GuildData(id=gid)
                self._guild_cache[gid].forced_nicks[str(row["user_id"])] = row["nickname"]
        except Exception as e:
            log.error("Failed to load forced_nicks: %s", e)

        # Load filter_config
        try:
            res = await client.table("filter_config").select("guild_id, filter_snipe").execute()
            for row in res.data or []:
                gid = int(row["guild_id"])
                if gid not in self._guild_cache:
                    self._guild_cache[gid] = GuildData(id=gid)
                self._guild_cache[gid].filter_snipe = row.get("filter_snipe") or False
        except Exception as e:
            log.error("Failed to load filter_config: %s", e)

        # Load jailed_members
        try:
            res = await client.table("jailed_members").select("guild_id, user_id").execute()
            for row in res.data or []:
                gid = int(row["guild_id"])
                if gid not in self._guild_cache:
                    self._guild_cache[gid] = GuildData(id=gid)
                uid = int(row["user_id"])
                if uid not in self._guild_cache[gid].jailed:
                    self._guild_cache[gid].jailed.append(uid)
        except Exception as e:
            log.error("Failed to load jailed_members: %s", e)

        log.info("Storage loaded: %d guild(s)", len(self._guild_cache))

    # ── GUILD ──────────────────────────────────────────────────────────────

    async def get_guild(self, guild_id: int) -> GuildData:
        """Get guild data, loading from Supabase if not cached."""
        if guild_id in self._guild_cache:
            return self._guild_cache[guild_id]

        client = await get_client()
        g = GuildData(id=guild_id)

        try:
            res = (
                await client.table("guild_config")
                .select("*")
                .eq("guild_id", guild_id)
                .maybe_single()
                .execute()
            )
            if res.data:
                _map_guild_config_row(g, res.data)
            else:
                await client.table("guild_config").insert(
                    {"guild_id": guild_id, "prefix": ","}
                ).execute()
        except Exception as e:
            log.error("Failed to get guild_config %s: %s", guild_id, e)

        # Load antinuke config
        try:
            res = (
                await client.table("antinuke_config")
                .select("*")
                .eq("guild_id", guild_id)
                .maybe_single()
                .execute()
            )
            if res.data:
                row = res.data
                g.antinuke_enabled = row.get("enabled") or False
                g.antinuke_kick = row.get("kick_protection") or False
                g.antinuke_ban = row.get("ban_protection") or False
                g.antinuke_vanity = row.get("vanity_protection") or False
                g.antinuke_guildupdate = row.get("guild_update") or False
                g.antinuke_botadd = row.get("bot_add") or False
        except Exception as e:
            log.error("Failed to get antinuke_config %s: %s", guild_id, e)

        # Load antinuke whitelist
        try:
            res = (
                await client.table("antinuke_whitelist")
                .select("user_id")
                .eq("guild_id", guild_id)
                .execute()
            )
            g.antinuke_whitelist = [int(r["user_id"]) for r in (res.data or [])]
        except Exception as e:
            log.error("Failed to get antinuke_whitelist %s: %s", guild_id, e)

        # Load antinuke admins
        try:
            res = (
                await client.table("antinuke_admins")
                .select("user_id")
                .eq("guild_id", guild_id)
                .execute()
            )
            g.antinuke_admins = [int(r["user_id"]) for r in (res.data or [])]
        except Exception as e:
            log.error("Failed to get antinuke_admins %s: %s", guild_id, e)

        # Load antiraid config
        try:
            res = (
                await client.table("antiraid_config")
                .select("*")
                .eq("guild_id", guild_id)
                .maybe_single()
                .execute()
            )
            if res.data:
                row = res.data
                g.antiraid_enabled = row.get("enabled") or False
                g.antiraid_massmention = row.get("massmention") or False
                g.antiraid_massjoin = row.get("massjoin") or False
                g.antiraid_age = row.get("age_protection") or False
                g.antiraid_avatar = row.get("avatar_protection") or False
                g.antiraid_unverifiedbots = row.get("unverified_bots") or False
        except Exception as e:
            log.error("Failed to get antiraid_config %s: %s", guild_id, e)

        # Load antiraid whitelist
        try:
            res = (
                await client.table("antiraid_whitelist")
                .select("user_id")
                .eq("guild_id", guild_id)
                .execute()
            )
            g.antiraid_whitelist = [int(r["user_id"]) for r in (res.data or [])]
        except Exception as e:
            log.error("Failed to get antiraid_whitelist %s: %s", guild_id, e)

        # Load antiraid username patterns
        try:
            res = (
                await client.table("antiraid_username_patterns")
                .select("pattern")
                .eq("guild_id", guild_id)
                .execute()
            )
            g.antiraid_username_patterns = [r["pattern"] for r in (res.data or [])]
        except Exception as e:
            log.error("Failed to get antiraid_username_patterns %s: %s", guild_id, e)

        # Load autoroles
        try:
            res = (
                await client.table("autoroles")
                .select("role_id, target_type")
                .eq("guild_id", guild_id)
                .execute()
            )
            for row in res.data or []:
                rid = int(row["role_id"])
                t = row.get("target_type", "all")
                if t == "human":
                    g.autoroles_human.append(rid)
                elif t == "bot":
                    g.autoroles_bot.append(rid)
                else:
                    g.autoroles.append(rid)
        except Exception as e:
            log.error("Failed to get autoroles %s: %s", guild_id, e)

        # Load voicecentre config
        try:
            res = (
                await client.table("voicecentre_config")
                .select("*")
                .eq("guild_id", guild_id)
                .maybe_single()
                .execute()
            )
            if res.data:
                row = res.data
                g.voicecenter_allowance = row.get("enabled") or False
                g.voicecenter_channel = row.get("create_channel_id")
                g.voicecenter_category = row.get("category_id")
                g.voicecenter_private_category = row.get("private_category_id")
                g.voicecenter_rolejoin = row.get("join_role_id")
                g.voicecenter_send_interface = row.get("send_interface") if row.get("send_interface") is not None else True
                g.voicecenter_default_name = row.get("default_name") or "{username} channel"
                g.voicecenter_default_bitrate = row.get("default_bitrate") or 64000
                g.voicecenter_default_region = row.get("default_region")
        except Exception as e:
            log.error("Failed to get voicecentre_config %s: %s", guild_id, e)

        # Load ticket config
        try:
            res = (
                await client.table("ticket_config")
                .select("*")
                .eq("guild_id", guild_id)
                .maybe_single()
                .execute()
            )
            if res.data:
                row = res.data
                g.ticket_category = row.get("category_id")
                g.ticket_support_role = row.get("support_role_id")
                g.ticket_log_channel = row.get("log_channel_id")
                g.ticket_welcome_message = row.get("welcome_message")
        except Exception as e:
            log.error("Failed to get ticket_config %s: %s", guild_id, e)

        # Load ticket managers
        try:
            res = (
                await client.table("ticket_managers")
                .select("target_id, target_type")
                .eq("guild_id", guild_id)
                .execute()
            )
            g.ticket_managers = [
                int(r["target_id"]) for r in (res.data or []) if r.get("target_type") == "user"
            ]
        except Exception as e:
            log.error("Failed to get ticket_managers %s: %s", guild_id, e)

        # Load booster role config
        try:
            res = (
                await client.table("booster_role_config")
                .select("*")
                .eq("guild_id", guild_id)
                .maybe_single()
                .execute()
            )
            if res.data:
                row = res.data
                g.booster_setup_enabled = row.get("enabled") or False
                g.booster_base_role = row.get("base_role_id")
                g.booster_base_position = row.get("base_position") or "below"
                g.booster_limit = row.get("role_limit") or 1
                g.booster_shares_limit = row.get("share_limit") or 5
                g.booster_shares_max = row.get("share_max") or 3
                g.booster_award_role = row.get("award_role_id")
                g.booster_hoist = row.get("hoist_new") if row.get("hoist_new") is not None else True
                bw = row.get("blacklisted_words")
                if bw:
                    g.booster_filters = list(bw)
        except Exception as e:
            log.error("Failed to get booster_role_config %s: %s", guild_id, e)

        # Load booster roles
        try:
            res = (
                await client.table("booster_roles")
                .select("user_id, role_id")
                .eq("guild_id", guild_id)
                .execute()
            )
            for row in res.data or []:
                g.booster_roles[str(row["user_id"])] = {"role_id": int(row["role_id"])}
        except Exception as e:
            log.error("Failed to get booster_roles %s: %s", guild_id, e)

        # Load warn_strikes
        try:
            res = (
                await client.table("warn_strikes")
                .select("strike, action")
                .eq("guild_id", guild_id)
                .execute()
            )
            for row in res.data or []:
                g.warn_strikes[str(row["strike"])] = {"action": row["action"]}
        except Exception as e:
            log.error("Failed to get warn_strikes %s: %s", guild_id, e)

        # Load fake_permissions
        try:
            res = (
                await client.table("fake_permissions")
                .select("role_id, permission")
                .eq("guild_id", guild_id)
                .execute()
            )
            for row in res.data or []:
                key = str(row["role_id"])
                if key not in g.fake_permissions:
                    g.fake_permissions[key] = []
                perm = row.get("permission")
                if perm and perm not in g.fake_permissions[key]:
                    g.fake_permissions[key].append(perm)
        except Exception as e:
            log.error("Failed to get fake_permissions %s: %s", guild_id, e)

        # Load forced_nicks
        try:
            res = (
                await client.table("forced_nicks")
                .select("user_id, nickname")
                .eq("guild_id", guild_id)
                .execute()
            )
            for row in res.data or []:
                g.forced_nicks[str(row["user_id"])] = row["nickname"]
        except Exception as e:
            log.error("Failed to get forced_nicks %s: %s", guild_id, e)

        # Load filter_config
        try:
            res = (
                await client.table("filter_config")
                .select("filter_snipe")
                .eq("guild_id", guild_id)
                .maybe_single()
                .execute()
            )
            if res.data:
                g.filter_snipe = res.data.get("filter_snipe") or False
        except Exception as e:
            log.error("Failed to get filter_config %s: %s", guild_id, e)

        # Load jailed members
        try:
            res = (
                await client.table("jailed_members")
                .select("user_id")
                .eq("guild_id", guild_id)
                .execute()
            )
            g.jailed = [int(r["user_id"]) for r in (res.data or [])]
        except Exception as e:
            log.error("Failed to get jailed_members %s: %s", guild_id, e)

        # Load AFK data
        try:
            res = (
                await client.table("afk")
                .select("user_id, status, set_at")
                .eq("guild_id", guild_id)
                .execute()
            )
            for row in res.data or []:
                uid = int(row["user_id"])
                set_at = row.get("set_at")
                since = (
                    datetime.fromisoformat(set_at).timestamp()
                    if set_at
                    else 0.0
                )
                g.afks[str(uid)] = {"reason": row.get("status") or "", "since": since}
        except Exception as e:
            log.error("Failed to get afk %s: %s", guild_id, e)

        self._guild_cache[guild_id] = g
        return g

    def get_guild_sync(self, guild_id: int) -> GuildData | None:
        """Get cached guild data synchronously."""
        return self._guild_cache.get(guild_id)

    async def save_guild(self, guild: GuildData) -> None:
        """Persist guild_config columns to Supabase."""
        self._guild_cache[guild.id] = guild
        client = await get_client()
        payload = {
            "guild_id": guild.id,
            "prefix": guild.prefix,
            "bot_lock": guild.bot_lock,
            "muted_role": guild.mute_role,
            "imuted_role": guild.imute_role,
            "rmuted_role": guild.rmute_role,
            "jail_channel": guild.jail_channel,
            "greet_enabled": guild.greet_enabled,
            "greet_channel": guild.greet_channel,
            "greet_msg": guild.greet_msg,
            "leave_enabled": guild.leave_enabled,
            "leave_channel": guild.leave_channel,
            "leave_msg": guild.leave_msg,
            "ping_enabled": guild.ping_enabled,
            "lockdown_staff_role": guild.lockdown_staff_role,
            "member_log_channel": guild.member_channel,
            "mod_log_channel": guild.mod_channel,
            "role_log_channel": guild.role_channel,
            "channel_log_channel": guild.channel_channel,
            "voice_log_channel": guild.voice_channel,
            "general_log_channel": guild.log_channel,
            "log_color": guild.log_color,
            "modlog_channel": guild.modlog_channel,
            "base_role": guild.base_role,
            "autonick": guild.autonick,
        }
        try:
            await client.table("guild_config").upsert(
                payload, on_conflict="guild_id"
            ).execute()
        except Exception as e:
            log.error("Failed to save guild %s: %s", guild.id, e)

    async def delete_guild(self, guild_id: int) -> None:
        """Delete guild data from Supabase."""
        self._guild_cache.pop(guild_id, None)
        self._guild_locks.pop(guild_id, None)
        client = await get_client()
        try:
            await client.table("guild_config").delete().eq(
                "guild_id", guild_id
            ).execute()
        except Exception as e:
            log.error("Failed to delete guild %s: %s", guild_id, e)

    async def update_setup(self, guild_id: int, **kwargs: Any) -> None:
        g = await self.get_guild(guild_id)
        for key, value in kwargs.items():
            if hasattr(g, key):
                setattr(g, key, value)
        await self.save_guild(g)

    # ── PREFIX ─────────────────────────────────────────────────────────────

    async def set_prefix(self, guild_id: int, prefix: str) -> None:
        g = await self.get_guild(guild_id)
        g.prefix = prefix
        await self.save_guild(g)

    # ── SUDO / BANS ────────────────────────────────────────────────────────

    def is_sudo(self, user_id: int) -> bool:
        return user_id in self.global_data.sudo_users

    def is_banned_guild(self, guild_id: int) -> bool:
        return guild_id in self.global_data.banned_guilds

    def is_banned_user(self, user_id: int) -> bool:
        return user_id in self.global_data.banned_users

    async def add_sudo(self, user_id: int) -> None:
        if user_id not in self.global_data.sudo_users:
            self.global_data.sudo_users.append(user_id)
        client = await get_client()
        try:
            await client.table("sudo_users").upsert(
                {"user_id": user_id, "granted_by": 0}, on_conflict="user_id"
            ).execute()
        except Exception as e:
            log.error("Failed to add sudo %s: %s", user_id, e)

    async def remove_sudo(self, user_id: int) -> None:
        if user_id in self.global_data.sudo_users:
            self.global_data.sudo_users.remove(user_id)
        client = await get_client()
        try:
            await client.table("sudo_users").delete().eq("user_id", user_id).execute()
        except Exception as e:
            log.error("Failed to remove sudo %s: %s", user_id, e)

    async def ban_guild(self, guild_id: int) -> None:
        if guild_id not in self.global_data.banned_guilds:
            self.global_data.banned_guilds.append(guild_id)
        client = await get_client()
        try:
            await client.table("guild_blacklist").insert(
                {"target_id": guild_id, "scope": "guild", "banned_by": 0}
            ).execute()
        except Exception as e:
            log.error("Failed to ban guild %s: %s", guild_id, e)

    async def unban_guild(self, guild_id: int) -> None:
        if guild_id in self.global_data.banned_guilds:
            self.global_data.banned_guilds.remove(guild_id)
        client = await get_client()
        try:
            await client.table("guild_blacklist").delete().eq("target_id", guild_id).eq(
                "scope", "guild"
            ).execute()
        except Exception as e:
            log.error("Failed to unban guild %s: %s", guild_id, e)

    async def ban_user(self, user_id: int) -> None:
        if user_id not in self.global_data.banned_users:
            self.global_data.banned_users.append(user_id)
        client = await get_client()
        try:
            await client.table("guild_blacklist").insert(
                {"target_id": user_id, "scope": "user", "banned_by": 0}
            ).execute()
        except Exception as e:
            log.error("Failed to ban user %s: %s", user_id, e)

    async def unban_user(self, user_id: int) -> None:
        if user_id in self.global_data.banned_users:
            self.global_data.banned_users.remove(user_id)
        client = await get_client()
        try:
            await client.table("guild_blacklist").delete().eq("target_id", user_id).eq(
                "scope", "user"
            ).execute()
        except Exception as e:
            log.error("Failed to unban user %s: %s", user_id, e)

    # ── AFK ────────────────────────────────────────────────────────────────

    async def set_afk(
        self, guild_id: int, user_id: int, reason: str, since: float
    ) -> None:
        g = await self.get_guild(guild_id)
        g.afks[str(user_id)] = {"reason": reason, "since": since}
        client = await get_client()
        set_at = datetime.fromtimestamp(since, tz=timezone.utc).isoformat()
        try:
            await client.table("afk").upsert(
                {
                    "user_id": user_id,
                    "guild_id": guild_id,
                    "status": reason,
                    "set_at": set_at,
                },
                on_conflict="user_id,guild_id",
            ).execute()
        except Exception as e:
            log.error("Failed to set afk %s/%s: %s", guild_id, user_id, e)

    async def clear_afk(self, guild_id: int, user_id: int) -> None:
        g = await self.get_guild(guild_id)
        g.afks.pop(str(user_id), None)
        client = await get_client()
        try:
            await client.table("afk").delete().eq("user_id", user_id).eq(
                "guild_id", guild_id
            ).execute()
        except Exception as e:
            log.error("Failed to clear afk %s/%s: %s", guild_id, user_id, e)

    # ── REACTION ROLES ─────────────────────────────────────────────────────

    async def add_reaction_role(self, guild_id: int, key: str, role_id: int) -> None:
        g = await self.get_guild(guild_id)
        g.reaction_roles[key] = role_id
        client = await get_client()
        try:
            parts = key.split(":")
            channel_id = int(parts[0]) if len(parts) > 0 else 0
            message_id = int(parts[1]) if len(parts) > 1 else 0
            reaction = parts[2] if len(parts) > 2 else key
            await client.table("reaction_roles").upsert(
                {
                    "guild_id": guild_id,
                    "channel_id": channel_id,
                    "message_id": message_id,
                    "reaction": reaction,
                    "role_id": role_id,
                },
                on_conflict="id",
            ).execute()
        except Exception as e:
            log.error("Failed to add reaction role %s: %s", guild_id, e)

    async def remove_reaction_role(self, guild_id: int, key: str) -> None:
        g = await self.get_guild(guild_id)
        g.reaction_roles.pop(key, None)
        client = await get_client()
        try:
            parts = key.split(":")
            message_id = int(parts[1]) if len(parts) > 1 else 0
            reaction = parts[2] if len(parts) > 2 else key
            await client.table("reaction_roles").delete().eq("guild_id", guild_id).eq(
                "message_id", message_id
            ).eq("reaction", reaction).execute()
        except Exception as e:
            log.error("Failed to remove reaction role %s: %s", guild_id, e)

    # ── VOICECENTER ────────────────────────────────────────────────────────

    async def _save_voicecenter_config(self, guild_id: int, g: GuildData) -> None:
        client = await get_client()
        try:
            await client.table("voicecentre_config").upsert(
                {
                    "guild_id": guild_id,
                    "enabled": g.voicecenter_allowance,
                    "create_channel_id": g.voicecenter_channel,
                    "category_id": g.voicecenter_category,
                    "private_category_id": g.voicecenter_private_category,
                    "join_role_id": g.voicecenter_rolejoin,
                    "send_interface": g.voicecenter_send_interface,
                    "default_name": g.voicecenter_default_name,
                    "default_bitrate": g.voicecenter_default_bitrate,
                    "default_region": g.voicecenter_default_region,
                },
                on_conflict="guild_id",
            ).execute()
        except Exception as e:
            log.error("Failed to save voicecentre_config %s: %s", guild_id, e)

    async def set_voicecenter_channel(self, guild_id: int, channel_id: int) -> None:
        g = await self.get_guild(guild_id)
        g.voicecenter_channel = channel_id
        await self._save_voicecenter_config(guild_id, g)

    async def set_voicecenter_category(self, guild_id: int, category_id: int) -> None:
        g = await self.get_guild(guild_id)
        g.voicecenter_category = category_id
        await self._save_voicecenter_config(guild_id, g)

    async def set_voicecenter_default(
        self, guild_id: int, key: str, value: Any
    ) -> None:
        g = await self.get_guild(guild_id)
        if not g.voicecenter_defaults:
            g.voicecenter_defaults = {}
        g.voicecenter_defaults[key] = value
        await self._save_voicecenter_config(guild_id, g)

    async def set_voicecenter_rolejoin(self, guild_id: int, role_id: int) -> None:
        g = await self.get_guild(guild_id)
        g.voicecenter_rolejoin = role_id
        await self._save_voicecenter_config(guild_id, g)

    async def clear_voicecenter(self, guild_id: int) -> None:
        g = await self.get_guild(guild_id)
        g.voicecenter_channel = None
        g.voicecenter_category = None
        g.voicecenter_private_category = None
        g.voicecenter_interface = None
        g.voicecenter_defaults.clear()
        g.voicecenter_rolejoin = None
        g.voicecenter_temp_channels.clear()
        g.voicecenter_allowance = False
        g.voicecenter_allowed.clear()
        g.voicecenter_disallowed.clear()
        g.voicecenter_systems.clear()
        await self._save_voicecenter_config(guild_id, g)

    # ── TICKET SYSTEM ──────────────────────────────────────────────────────

    async def _save_ticket_config(self, guild_id: int, g: GuildData) -> None:
        client = await get_client()
        try:
            await client.table("ticket_config").upsert(
                {
                    "guild_id": guild_id,
                    "category_id": g.ticket_category,
                    "support_role_id": g.ticket_support_role,
                    "log_channel_id": g.ticket_log_channel,
                    "welcome_message": g.ticket_welcome_message,
                },
                on_conflict="guild_id",
            ).execute()
        except Exception as e:
            log.error("Failed to save ticket_config %s: %s", guild_id, e)

    async def set_ticket_channel(self, guild_id: int, channel_id: int) -> None:
        g = await self.get_guild(guild_id)
        g.ticket_channel = channel_id
        g.ticket_category = channel_id
        await self._save_ticket_config(guild_id, g)

    async def add_ticket_manager(self, guild_id: int, user_id: int) -> None:
        g = await self.get_guild(guild_id)
        if user_id not in g.ticket_managers:
            g.ticket_managers.append(user_id)
        client = await get_client()
        try:
            await client.table("ticket_managers").upsert(
                {"guild_id": guild_id, "target_id": user_id, "target_type": "user"},
                on_conflict="id",
            ).execute()
        except Exception as e:
            log.error("Failed to add ticket_manager %s: %s", guild_id, e)

    async def remove_ticket_manager(self, guild_id: int, user_id: int) -> None:
        g = await self.get_guild(guild_id)
        if user_id in g.ticket_managers:
            g.ticket_managers.remove(user_id)
        client = await get_client()
        try:
            await client.table("ticket_managers").delete().eq("guild_id", guild_id).eq(
                "target_id", user_id
            ).eq("target_type", "user").execute()
        except Exception as e:
            log.error("Failed to remove ticket_manager %s: %s", guild_id, e)

    # ── AUTOROLE METHODS ───────────────────────────────────────────────────

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
        client = await get_client()
        try:
            await client.table("autoroles").insert(
                {"guild_id": guild_id, "role_id": role_id, "target_type": target}
            ).execute()
        except Exception as e:
            log.error("Failed to add autorole %s: %s", guild_id, e)

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
        client = await get_client()
        try:
            await client.table("autoroles").delete().eq("guild_id", guild_id).eq(
                "role_id", role_id
            ).eq("target_type", target).execute()
        except Exception as e:
            log.error("Failed to remove autorole %s: %s", guild_id, e)

    # ── BUTTON ROLES METHODS ───────────────────────────────────────────────

    async def add_button_role(self, guild_id: int, key: str, role_id: int) -> None:
        g = await self.get_guild(guild_id)
        g.button_roles[key] = role_id
        client = await get_client()
        try:
            parts = key.split(":")
            channel_id = int(parts[0]) if len(parts) > 0 else 0
            message_id = int(parts[1]) if len(parts) > 1 else 0
            await client.table("button_roles").insert(
                {
                    "guild_id": guild_id,
                    "channel_id": channel_id,
                    "message_id": message_id,
                    "role_id": role_id,
                }
            ).execute()
        except Exception as e:
            log.error("Failed to add button_role %s: %s", guild_id, e)

    async def remove_button_role(self, guild_id: int, key: str) -> None:
        g = await self.get_guild(guild_id)
        g.button_roles.pop(key, None)
        client = await get_client()
        try:
            parts = key.split(":")
            message_id = int(parts[1]) if len(parts) > 1 else 0
            await client.table("button_roles").delete().eq("guild_id", guild_id).eq(
                "message_id", message_id
            ).execute()
        except Exception as e:
            log.error("Failed to remove button_role %s: %s", guild_id, e)

    # ── BOOSTER ROLE METHODS ───────────────────────────────────────────────

    async def _save_booster_config(self, guild_id: int, g: GuildData) -> None:
        client = await get_client()
        try:
            await client.table("booster_role_config").upsert(
                {
                    "guild_id": guild_id,
                    "enabled": g.booster_setup_enabled,
                    "base_role_id": g.booster_base_role,
                    "base_position": g.booster_base_position,
                    "role_limit": g.booster_limit,
                    "share_limit": g.booster_shares_limit,
                    "share_max": g.booster_shares_max,
                    "award_role_id": g.booster_award_role,
                    "hoist_new": g.booster_hoist,
                    "blacklisted_words": g.booster_filters,
                },
                on_conflict="guild_id",
            ).execute()
        except Exception as e:
            log.error("Failed to save booster_role_config %s: %s", guild_id, e)

    async def add_booster_role(
        self, guild_id: int, user_id: int, role_info: dict[str, Any]
    ) -> None:
        g = await self.get_guild(guild_id)
        g.booster_roles[str(user_id)] = role_info
        client = await get_client()
        try:
            await client.table("booster_roles").insert(
                {
                    "guild_id": guild_id,
                    "user_id": user_id,
                    "role_id": role_info.get("role_id", 0),
                }
            ).execute()
        except Exception as e:
            log.error("Failed to add booster_role %s: %s", guild_id, e)

    async def remove_booster_role(self, guild_id: int, user_id: int) -> None:
        g = await self.get_guild(guild_id)
        g.booster_roles.pop(str(user_id), None)
        client = await get_client()
        try:
            await client.table("booster_roles").delete().eq("guild_id", guild_id).eq(
                "user_id", user_id
            ).execute()
        except Exception as e:
            log.error("Failed to remove booster_role %s: %s", guild_id, e)

    # ── FRIEND GROUP METHODS ───────────────────────────────────────────────

    async def add_friend_group(
        self, guild_id: int, name: str, group_info: dict[str, Any]
    ) -> None:
        g = await self.get_guild(guild_id)
        g.fg_list[name] = group_info
        client = await get_client()
        try:
            await client.table("friend_groups").insert(
                {
                    "guild_id": guild_id,
                    "name": name,
                    "member_limit": group_info.get("member_limit", 10),
                    "owner_id": group_info.get("owner_id"),
                    "role_id": group_info.get("role_id"),
                    "vc_id": group_info.get("vc_id"),
                }
            ).execute()
        except Exception as e:
            log.error("Failed to add friend_group %s: %s", guild_id, e)

    async def remove_friend_group(self, guild_id: int, name: str) -> None:
        g = await self.get_guild(guild_id)
        g.fg_list.pop(name, None)
        client = await get_client()
        try:
            await client.table("friend_groups").delete().eq("guild_id", guild_id).eq(
                "name", name
            ).execute()
        except Exception as e:
            log.error("Failed to remove friend_group %s: %s", guild_id, e)

    # ── GREET/LEAVE METHODS ────────────────────────────────────────────────

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

    # ── PING ON JOIN METHODS ───────────────────────────────────────────────

    async def add_ping_assignment(
        self, guild_id: int, channel_id: int, config: dict[str, Any]
    ) -> None:
        g = await self.get_guild(guild_id)
        g.ping_assignments[str(channel_id)] = config
        client = await get_client()
        try:
            await client.table("ping_assignments").upsert(
                {
                    "guild_id": guild_id,
                    "channel_id": channel_id,
                    "autodelete": config.get("autodelete", 3),
                },
                on_conflict="id",
            ).execute()
        except Exception as e:
            log.error("Failed to add ping_assignment %s: %s", guild_id, e)

    async def remove_ping_assignment(self, guild_id: int, channel_id: int) -> None:
        g = await self.get_guild(guild_id)
        g.ping_assignments.pop(str(channel_id), None)
        client = await get_client()
        try:
            await client.table("ping_assignments").delete().eq("guild_id", guild_id).eq(
                "channel_id", channel_id
            ).execute()
        except Exception as e:
            log.error("Failed to remove ping_assignment %s: %s", guild_id, e)

    # ── LEVEL METHODS ──────────────────────────────────────────────────────

    async def _save_level_config(self, guild_id: int, g: GuildData) -> None:
        client = await get_client()
        try:
            await client.table("level_config").upsert(
                {
                    "guild_id": guild_id,
                    "enabled": g.levels_enabled,
                    "xp_multiplier": g.levels_xp_multiplier,
                    "message_mode": g.levels_message_mode,
                    "channel_id": g.levels_channel,
                    "levelup_msg": g.levels_msg,
                    "stack_roles": g.levels_stack_roles,
                },
                on_conflict="guild_id",
            ).execute()
        except Exception as e:
            log.error("Failed to save level_config %s: %s", guild_id, e)

    async def add_level(self, guild_id: int, level: int, role_id: int) -> None:
        g = await self.get_guild(guild_id)
        g.levels_list.append({"level": level, "role_id": role_id})
        client = await get_client()
        try:
            await client.table("level_roles").insert(
                {"guild_id": guild_id, "role_id": role_id, "level": level}
            ).execute()
        except Exception as e:
            log.error("Failed to add level_role %s: %s", guild_id, e)

    async def remove_level(self, guild_id: int, level: int) -> None:
        g = await self.get_guild(guild_id)
        g.levels_list = [l for l in g.levels_list if l.get("level") != level]
        client = await get_client()
        try:
            await client.table("level_roles").delete().eq("guild_id", guild_id).eq(
                "level", level
            ).execute()
        except Exception as e:
            log.error("Failed to remove level_role %s: %s", guild_id, e)

    async def add_xp(self, guild_id: int, user_id: int, amount: int) -> None:
        g = await self.get_guild(guild_id)
        current = g.levels_xp_leaderboard.get(str(user_id), 0)
        new_total = current + amount
        g.levels_xp_leaderboard[str(user_id)] = new_total
        client = await get_client()
        try:
            res = (
                await client.table("levels")
                .select("xp, level, total_xp")
                .eq("guild_id", guild_id)
                .eq("user_id", user_id)
                .maybe_single()
                .execute()
            )
            if res.data:
                new_xp = res.data["xp"] + amount
                new_lvl = self.xp_to_level(res.data["total_xp"] + amount)
                await client.table("levels").update(
                    {"xp": new_xp, "level": new_lvl, "total_xp": res.data["total_xp"] + amount}
                ).eq("guild_id", guild_id).eq("user_id", user_id).execute()
            else:
                await client.table("levels").insert(
                    {"guild_id": guild_id, "user_id": user_id, "xp": amount, "level": 0, "total_xp": amount}
                ).execute()
        except Exception as e:
            log.error("Failed to add_xp %s/%s: %s", guild_id, user_id, e)

    def get_user_xp(self, g: GuildData, user_id: int) -> int:
        return g.levels_xp_leaderboard.get(str(user_id), 0)

    def xp_to_level(self, xp: int) -> int:
        level = 0
        while xp >= self.level_to_xp(level + 1):
            level += 1
        return level

    def level_to_xp(self, level: int) -> int:
        return 5 * (level**2) + 50 * level + 100

    # ── TIMER METHODS ──────────────────────────────────────────────────────

    async def add_timer(
        self, guild_id: int, timer_id: str, config: dict[str, Any]
    ) -> None:
        g = await self.get_guild(guild_id)
        g.timers[timer_id] = config
        client = await get_client()
        try:
            await client.table("timers").insert(
                {
                    "guild_id": guild_id,
                    "channel_id": config.get("channel_id", 0),
                    "message": config.get("message", ""),
                    "interval_secs": config.get("interval_secs", 3600),
                    "require_activity": config.get("require_activity", False),
                }
            ).execute()
        except Exception as e:
            log.error("Failed to add timer %s: %s", guild_id, e)

    async def remove_timer(self, guild_id: int, timer_id: str) -> None:
        g = await self.get_guild(guild_id)
        config = g.timers.pop(timer_id, {})
        client = await get_client()
        try:
            channel_id = config.get("channel_id")
            if channel_id:
                await client.table("timers").delete().eq("guild_id", guild_id).eq(
                    "channel_id", channel_id
                ).execute()
        except Exception as e:
            log.error("Failed to remove timer %s: %s", guild_id, e)

    # ── COUNTER METHODS ────────────────────────────────────────────────────

    async def add_counter(self, guild_id: int, channel_id: int) -> None:
        g = await self.get_guild(guild_id)
        g.counters[str(channel_id)] = {"count": 0, "paused": False}
        client = await get_client()
        try:
            await client.table("counters").insert(
                {"guild_id": guild_id, "channel_id": channel_id, "type": "general"}
            ).execute()
        except Exception as e:
            log.error("Failed to add counter %s: %s", guild_id, e)

    async def remove_counter(self, guild_id: int, channel_id: int) -> None:
        g = await self.get_guild(guild_id)
        g.counters.pop(str(channel_id), None)
        client = await get_client()
        try:
            await client.table("counters").delete().eq("guild_id", guild_id).eq(
                "channel_id", channel_id
            ).execute()
        except Exception as e:
            log.error("Failed to remove counter %s: %s", guild_id, e)

    # ── REMINDER METHODS ───────────────────────────────────────────────────

    async def add_reminder(
        self, guild_id: int, reminder_id: str, config: dict[str, Any]
    ) -> None:
        g = await self.get_guild(guild_id)
        g.reminders[reminder_id] = config
        client = await get_client()
        try:
            remind_at_ts = config.get("remind_at")
            remind_at = (
                datetime.fromtimestamp(remind_at_ts, tz=timezone.utc).isoformat()
                if remind_at_ts
                else datetime.now(tz=timezone.utc).isoformat()
            )
            await client.table("reminders").insert(
                {
                    "user_id": config.get("user_id", 0),
                    "guild_id": guild_id,
                    "channel_id": config.get("channel_id"),
                    "content": config.get("content", ""),
                    "remind_at": remind_at,
                }
            ).execute()
        except Exception as e:
            log.error("Failed to add reminder %s: %s", guild_id, e)

    async def remove_reminder(self, guild_id: int, reminder_id: str) -> None:
        g = await self.get_guild(guild_id)
        g.reminders.pop(reminder_id, None)
        client = await get_client()
        try:
            await client.table("reminders").delete().eq("id", reminder_id).execute()
        except Exception as e:
            log.error("Failed to remove reminder %s: %s", guild_id, e)

    # ── WARNING METHODS ────────────────────────────────────────────────────

    async def add_warning(
        self, guild_id: int, user_id: int, warning_info: dict[str, Any]
    ) -> None:
        g = await self.get_guild(guild_id)
        key = str(user_id)
        if key not in g.warnings:
            g.warnings[key] = []
        g.warnings[key].append(warning_info)
        client = await get_client()
        try:
            await client.table("warnings").insert(
                {
                    "guild_id": guild_id,
                    "target_id": user_id,
                    "moderator_id": warning_info.get("moderator_id", 0),
                    "reason": warning_info.get("reason"),
                }
            ).execute()
        except Exception as e:
            log.error("Failed to add warning %s: %s", guild_id, e)

    async def clear_warnings(self, guild_id: int, user_id: int) -> None:
        g = await self.get_guild(guild_id)
        g.warnings.pop(str(user_id), None)
        client = await get_client()
        try:
            await client.table("warnings").delete().eq("guild_id", guild_id).eq(
                "target_id", user_id
            ).execute()
        except Exception as e:
            log.error("Failed to clear warnings %s: %s", guild_id, e)

    # ── ANTINUKE METHODS ───────────────────────────────────────────────────

    async def _save_antinuke_config(self, guild_id: int, g: GuildData) -> None:
        client = await get_client()
        try:
            await client.table("antinuke_config").upsert(
                {
                    "guild_id": guild_id,
                    "enabled": g.antinuke_enabled,
                    "kick_protection": g.antinuke_kick,
                    "ban_protection": g.antinuke_ban,
                    "vanity_protection": g.antinuke_vanity,
                    "guild_update": g.antinuke_guildupdate,
                    "bot_add": g.antinuke_botadd,
                },
                on_conflict="guild_id",
            ).execute()
        except Exception as e:
            log.error("Failed to save antinuke_config %s: %s", guild_id, e)

    async def set_antinuke(self, guild_id: int, **kwargs: Any) -> None:
        g = await self.get_guild(guild_id)
        for key, value in kwargs.items():
            if hasattr(g, key):
                setattr(g, key, value)
        await self._save_antinuke_config(guild_id, g)

    async def add_antinuke_whitelist(self, guild_id: int, user_id: int) -> None:
        g = await self.get_guild(guild_id)
        if user_id not in g.antinuke_whitelist:
            g.antinuke_whitelist.append(user_id)
        client = await get_client()
        try:
            await client.table("antinuke_whitelist").upsert(
                {"guild_id": guild_id, "user_id": user_id},
                on_conflict="guild_id,user_id",
            ).execute()
        except Exception as e:
            log.error("Failed to add antinuke_whitelist %s: %s", guild_id, e)

    async def remove_antinuke_whitelist(self, guild_id: int, user_id: int) -> None:
        g = await self.get_guild(guild_id)
        if user_id in g.antinuke_whitelist:
            g.antinuke_whitelist.remove(user_id)
        client = await get_client()
        try:
            await client.table("antinuke_whitelist").delete().eq("guild_id", guild_id).eq(
                "user_id", user_id
            ).execute()
        except Exception as e:
            log.error("Failed to remove antinuke_whitelist %s: %s", guild_id, e)

    async def add_antinuke_admin(self, guild_id: int, user_id: int) -> None:
        g = await self.get_guild(guild_id)
        if user_id not in g.antinuke_admins:
            g.antinuke_admins.append(user_id)
        client = await get_client()
        try:
            await client.table("antinuke_admins").upsert(
                {"guild_id": guild_id, "user_id": user_id},
                on_conflict="guild_id,user_id",
            ).execute()
        except Exception as e:
            log.error("Failed to add antinuke_admin %s: %s", guild_id, e)

    async def remove_antinuke_admin(self, guild_id: int, user_id: int) -> None:
        g = await self.get_guild(guild_id)
        if user_id in g.antinuke_admins:
            g.antinuke_admins.remove(user_id)
        client = await get_client()
        try:
            await client.table("antinuke_admins").delete().eq("guild_id", guild_id).eq(
                "user_id", user_id
            ).execute()
        except Exception as e:
            log.error("Failed to remove antinuke_admin %s: %s", guild_id, e)

    # ── ANTIRAID METHODS ───────────────────────────────────────────────────

    async def _save_antiraid_config(self, guild_id: int, g: GuildData) -> None:
        client = await get_client()
        try:
            await client.table("antiraid_config").upsert(
                {
                    "guild_id": guild_id,
                    "enabled": g.antiraid_enabled,
                    "massmention": g.antiraid_massmention,
                    "massjoin": g.antiraid_massjoin,
                    "age_protection": g.antiraid_age,
                    "avatar_protection": g.antiraid_avatar,
                    "unverified_bots": g.antiraid_unverifiedbots,
                },
                on_conflict="guild_id",
            ).execute()
        except Exception as e:
            log.error("Failed to save antiraid_config %s: %s", guild_id, e)

    async def set_antiraid(self, guild_id: int, **kwargs: Any) -> None:
        g = await self.get_guild(guild_id)
        for key, value in kwargs.items():
            if hasattr(g, key):
                setattr(g, key, value)
        await self._save_antiraid_config(guild_id, g)

    async def add_antiraid_whitelist(self, guild_id: int, user_id: int) -> None:
        g = await self.get_guild(guild_id)
        if user_id not in g.antiraid_whitelist:
            g.antiraid_whitelist.append(user_id)
        client = await get_client()
        try:
            await client.table("antiraid_whitelist").upsert(
                {"guild_id": guild_id, "user_id": user_id},
                on_conflict="guild_id,user_id",
            ).execute()
        except Exception as e:
            log.error("Failed to add antiraid_whitelist %s: %s", guild_id, e)

    async def remove_antiraid_whitelist(self, guild_id: int, user_id: int) -> None:
        g = await self.get_guild(guild_id)
        if user_id in g.antiraid_whitelist:
            g.antiraid_whitelist.remove(user_id)
        client = await get_client()
        try:
            await client.table("antiraid_whitelist").delete().eq("guild_id", guild_id).eq(
                "user_id", user_id
            ).execute()
        except Exception as e:
            log.error("Failed to remove antiraid_whitelist %s: %s", guild_id, e)

    async def add_antiraid_pattern(self, guild_id: int, pattern: str) -> None:
        g = await self.get_guild(guild_id)
        if pattern not in g.antiraid_username_patterns:
            g.antiraid_username_patterns.append(pattern)
        client = await get_client()
        try:
            await client.table("antiraid_username_patterns").insert(
                {"guild_id": guild_id, "pattern": pattern}
            ).execute()
        except Exception as e:
            log.error("Failed to add antiraid_pattern %s: %s", guild_id, e)

    async def remove_antiraid_pattern(self, guild_id: int, pattern: str) -> None:
        g = await self.get_guild(guild_id)
        if pattern in g.antiraid_username_patterns:
            g.antiraid_username_patterns.remove(pattern)
        client = await get_client()
        try:
            await client.table("antiraid_username_patterns").delete().eq(
                "guild_id", guild_id
            ).eq("pattern", pattern).execute()
        except Exception as e:
            log.error("Failed to remove antiraid_pattern %s: %s", guild_id, e)

    # ── JAIL METHODS ───────────────────────────────────────────────────────

    async def jail_member(self, guild_id: int, user_id: int) -> None:
        g = await self.get_guild(guild_id)
        if user_id not in g.jailed:
            g.jailed.append(user_id)
        client = await get_client()
        try:
            await client.table("jailed_members").upsert(
                {"guild_id": guild_id, "user_id": user_id},
                on_conflict="guild_id,user_id",
            ).execute()
        except Exception as e:
            log.error("Failed to jail member %s/%s: %s", guild_id, user_id, e)

    async def unjail_member(self, guild_id: int, user_id: int) -> None:
        g = await self.get_guild(guild_id)
        if user_id in g.jailed:
            g.jailed.remove(user_id)
        client = await get_client()
        try:
            await client.table("jailed_members").delete().eq("guild_id", guild_id).eq(
                "user_id", user_id
            ).execute()
        except Exception as e:
            log.error("Failed to unjail member %s/%s: %s", guild_id, user_id, e)

    # ── FORCED NICK METHODS ────────────────────────────────────────────────

    async def set_forced_nick(self, guild_id: int, user_id: int, nickname: str) -> None:
        g = await self.get_guild(guild_id)
        g.forced_nicks[str(user_id)] = nickname
        client = await get_client()
        try:
            await client.table("forced_nicks").upsert(
                {"guild_id": guild_id, "user_id": user_id, "nickname": nickname},
                on_conflict="guild_id,user_id",
            ).execute()
        except Exception as e:
            log.error("Failed to set forced_nick %s/%s: %s", guild_id, user_id, e)

    async def clear_forced_nick(self, guild_id: int, user_id: int) -> None:
        g = await self.get_guild(guild_id)
        g.forced_nicks.pop(str(user_id), None)
        client = await get_client()
        try:
            await client.table("forced_nicks").delete().eq("guild_id", guild_id).eq(
                "user_id", user_id
            ).execute()
        except Exception as e:
            log.error("Failed to clear forced_nick %s/%s: %s", guild_id, user_id, e)

    # ── FILTER METHODS ─────────────────────────────────────────────────────

    async def set_filter_snipe(self, guild_id: int, value: bool) -> None:
        g = await self.get_guild(guild_id)
        g.filter_snipe = value
        client = await get_client()
        try:
            await client.table("filter_config").upsert(
                {"guild_id": guild_id, "filter_snipe": value},
                on_conflict="guild_id",
            ).execute()
        except Exception as e:
            log.error("Failed to set filter_snipe %s: %s", guild_id, e)

    async def add_filter(self, guild_id: int, filter_type: str, value: str, channel_id: int | None = None, setting: str | None = None) -> None:
        g = await self.get_guild(guild_id)
        attr_map = {
            "keyword": "keyword_filters",
            "link": "link_filters",
            "invite": "invite_filters",
            "regex": "regex_filters",
            "nickname": "nickname_filters",
        }
        attr = attr_map.get(filter_type)
        if attr and hasattr(g, attr):
            lst = getattr(g, attr)
            if value not in lst:
                lst.append(value)
        client = await get_client()
        try:
            await client.table("filters").insert(
                {
                    "guild_id": guild_id,
                    "type": filter_type,
                    "value": value,
                    "channel_id": channel_id,
                    "setting": setting,
                }
            ).execute()
        except Exception as e:
            log.error("Failed to add filter %s: %s", guild_id, e)

    async def remove_filter(self, guild_id: int, filter_type: str, value: str) -> None:
        g = await self.get_guild(guild_id)
        attr_map = {
            "keyword": "keyword_filters",
            "link": "link_filters",
            "invite": "invite_filters",
            "regex": "regex_filters",
            "nickname": "nickname_filters",
        }
        attr = attr_map.get(filter_type)
        if attr and hasattr(g, attr):
            lst = getattr(g, attr)
            if value in lst:
                lst.remove(value)
        client = await get_client()
        try:
            await client.table("filters").delete().eq("guild_id", guild_id).eq(
                "type", filter_type
            ).eq("value", value).execute()
        except Exception as e:
            log.error("Failed to remove filter %s: %s", guild_id, e)

    # ── STICKY MESSAGE METHODS ─────────────────────────────────────────────

    async def add_sticky_message(self, guild_id: int, channel_id: int, message: str) -> None:
        g = await self.get_guild(guild_id)
        g.sticky_messages[str(channel_id)] = {"message": message}
        client = await get_client()
        try:
            await client.table("sticky_messages").insert(
                {"guild_id": guild_id, "channel_id": channel_id, "message": message}
            ).execute()
        except Exception as e:
            log.error("Failed to add sticky_message %s: %s", guild_id, e)

    async def remove_sticky_message(self, guild_id: int, channel_id: int) -> None:
        g = await self.get_guild(guild_id)
        g.sticky_messages.pop(str(channel_id), None)
        client = await get_client()
        try:
            await client.table("sticky_messages").delete().eq("guild_id", guild_id).eq(
                "channel_id", channel_id
            ).execute()
        except Exception as e:
            log.error("Failed to remove sticky_message %s: %s", guild_id, e)

    # ── AUTORESPONDER METHODS ──────────────────────────────────────────────

    async def add_autoresponder(self, guild_id: int, trigger: str, response: str, owner_id: int) -> None:
        g = await self.get_guild(guild_id)
        g.autoresponders[trigger] = {"response": response, "owner_id": owner_id}
        client = await get_client()
        try:
            await client.table("autoresponders").insert(
                {
                    "guild_id": guild_id,
                    "trigger": trigger,
                    "response": response,
                    "owner_id": owner_id,
                }
            ).execute()
        except Exception as e:
            log.error("Failed to add autoresponder %s: %s", guild_id, e)

    async def remove_autoresponder(self, guild_id: int, trigger: str) -> None:
        g = await self.get_guild(guild_id)
        g.autoresponders.pop(trigger, None)
        client = await get_client()
        try:
            await client.table("autoresponders").delete().eq("guild_id", guild_id).eq(
                "trigger", trigger
            ).execute()
        except Exception as e:
            log.error("Failed to remove autoresponder %s: %s", guild_id, e)

    # ── WARN STRIKE METHODS ────────────────────────────────────────────────

    async def set_warn_strike(self, guild_id: int, strike: int, action: str) -> None:
        g = await self.get_guild(guild_id)
        g.warn_strikes[str(strike)] = {"action": action}
        client = await get_client()
        try:
            await client.table("warn_strikes").upsert(
                {"guild_id": guild_id, "strike": strike, "action": action},
                on_conflict="guild_id,strike",
            ).execute()
        except Exception as e:
            log.error("Failed to set warn_strike %s: %s", guild_id, e)

    async def remove_warn_strike(self, guild_id: int, strike: int) -> None:
        g = await self.get_guild(guild_id)
        g.warn_strikes.pop(str(strike), None)
        client = await get_client()
        try:
            await client.table("warn_strikes").delete().eq("guild_id", guild_id).eq(
                "strike", strike
            ).execute()
        except Exception as e:
            log.error("Failed to remove warn_strike %s: %s", guild_id, e)

    # ── FAKE PERMISSIONS METHODS ───────────────────────────────────────────

    async def add_fake_permission(self, guild_id: int, role_id: int, permission: str) -> None:
        g = await self.get_guild(guild_id)
        key = str(role_id)
        if key not in g.fake_permissions:
            g.fake_permissions[key] = []
        if permission not in g.fake_permissions[key]:
            g.fake_permissions[key].append(permission)
        client = await get_client()
        try:
            await client.table("fake_permissions").insert(
                {"guild_id": guild_id, "role_id": role_id, "permission": permission}
            ).execute()
        except Exception as e:
            log.error("Failed to add fake_permission %s: %s", guild_id, e)

    async def remove_fake_permission(self, guild_id: int, role_id: int, permission: str) -> None:
        g = await self.get_guild(guild_id)
        key = str(role_id)
        if key in g.fake_permissions and permission in g.fake_permissions[key]:
            g.fake_permissions[key].remove(permission)
        client = await get_client()
        try:
            await client.table("fake_permissions").delete().eq("guild_id", guild_id).eq(
                "role_id", role_id
            ).eq("permission", permission).execute()
        except Exception as e:
            log.error("Failed to remove fake_permission %s: %s", guild_id, e)
