# Pushie Bot — Command Structure Reference

Comprehensive command structure and organization guide for the Pushie Discord bot. This document details all commands, their parameters, hierarchy, aliases, and implementation status.

## 📋 Code Architecture Standards

### Hybrid Commands (Required)

All commands must use `@commands.hybrid_command()` to support both prefix and slash usage.

```python
@commands.hybrid_command(name="cmd_name", description="What it does")
async def cmd_name(self, ctx: "PushieContext", arg: str) -> None:
    await ctx.ok("Success!")
```

### Type Hints (Required)

All parameters must include type hints for automatic conversion.

### Context Methods (Standard UI)

- `ctx.ok(msg)` — Green success embed
- `ctx.err(msg)` — Red error embed
- `ctx.warn(msg)` — Yellow warning embed
- `ctx.info(msg)` — Blue info embed
- `ctx.afk(msg)` — AFK-specific embed

### Permission Decorators

```python
@commands.guild_only()                          # Server only
@commands.has_permissions(manage_guild=True)    # User permission
@commands.has_guild_permissions(moderate_members=True)  # Guild permission
```

### Error Handling (Per Cog)

```python
async def cog_command_error(self, ctx: commands.Context, error: Exception) -> None:
    if isinstance(error, commands.MissingPermissions):
        await ctx.err(f"You need: {error.missing_permissions}")
    else:
        raise error
```

---

## 🎯 Complete Command Reference

### **CORE Commands** (`main.py`) — 16 total

**Prefix:** `!` (configurable per guild)  
**Slash:** `/`

#### Regular Commands

| Command  | Aliases | Parameters                | Permissions   | Status         |
| -------- | ------- | ------------------------- | ------------- | -------------- |
| `ping`   | —       | —                         | —             | ✅ Implemented |
| `afk`    | —       | `reason: str = "AFK"`     | Guild only    | ✅ Implemented |
| `help`   | —       | `command: str \| None`    | —             | ✅ Implemented |
| `prefix` | —       | `new_prefix: str \| None` | Manage Server | ✅ Implemented |

#### Command Group: `sudo`

**Permission:** `is_sudo()` (check decorator)

| Subcommand    | Parameters           | Purpose                          |
| ------------- | -------------------- | -------------------------------- |
| `reload`      | `ext: str`           | Reload a cog extension           |
| `load`        | `ext: str`           | Load a cog extension             |
| `unload`      | `ext: str`           | Unload a cog extension           |
| `sync`        | —                    | Sync slash commands globally     |
| `stats`       | —                    | Show bot CPU/memory/uptime stats |
| `ban_guild`   | `guild_id: int`      | Ban guild from using bot         |
| `unban_guild` | `guild_id: int`      | Unban guild                      |
| `ban_user`    | `user: discord.User` | Ban user from using bot          |
| `unban_user`  | `user: discord.User` | Unban user                       |
| `add_sudo`    | `user: discord.User` | Add sudo access                  |
| `remove_sudo` | `user: discord.User` | Remove sudo access               |
| `shutdown`    | —                    | Gracefully shutdown bot          |

---

### **INFO Commands** (`info.py`) — 17 total

**Cog Name:** Info  
**Features:** User/server/channel info, image processing

#### Regular Commands

| Command       | Aliases | Parameters                                  | Permissions | Status         |
| ------------- | ------- | ------------------------------------------- | ----------- | -------------- |
| `serverinfo`  | `si`    | —                                           | Guild only  | ✅ Implemented |
| `channelinfo` | `ci`    | `channel: discord.abc.GuildChannel \| None` | Guild only  | ✅ Implemented |
| `userinfo`    | `ui`    | `member: discord.Member \| None`            | Guild only  | ✅ Implemented |
| `botinfo`     | `bi`    | —                                           | —           | ✅ Implemented |
| `banner`      | `bn`    | `user: discord.User \| None`                | —           | ✅ Implemented |
| `avatar`      | `av`    | `user: discord.User \| None`                | —           | ✅ Implemented |
| `sbanner`     | `sbn`   | `member: discord.Member \| None`            | Guild only  | ✅ Implemented |
| `sav`         | —       | `member: discord.Member \| None`            | Guild only  | ✅ Implemented |

#### Command Group: `icon` (aliases: `ic`)

| Subcommand | Parameters          | Permissions      |
| ---------- | ------------------- | ---------------- |
| (view)     | —                   | Guild only, none |
| `set`      | `link: str \| None` | Manage Guild     |

#### Command Group: `gbanner` (aliases: `gbn`)

| Subcommand | Parameters          | Permissions             |
| ---------- | ------------------- | ----------------------- |
| (view)     | —                   | Guild only, none        |
| `set`      | `link: str \| None` | Manage Guild, Boost L2+ |

#### Command Group: `image` (aliases: `img`)

| Subcommand | Parameters            | Purpose                    |
| ---------- | --------------------- | -------------------------- |
| `darken`   | `factor: float = 0.4` | Darken image (0.0-1.0)     |
| `lighten`  | `factor: float = 0.4` | Lighten image (0.0-1.0)    |
| `round`    | —                     | Round-crop image to circle |

_Image commands require attached image or reply to message with image_

---

### **SPOTIFY Commands** (`spotify.py`) — 5 total

**Cog Name:** Spotify  
**Features:** Account linking, now playing, playlist management  
**Status:** Partially implemented

#### Command Group: `spotify`

| Subcommand | Parameters                 | Feature                                |
| ---------- | -------------------------- | -------------------------------------- |
| `link`     | `username: str`            | Link Spotify account                   |
| `now`      | —                          | Show currently playing (with controls) |
| `playlist` | `action: str`, `name: str` | Create/manage playlists                |
| `search`   | `query: str`               | Search Spotify for track               |
| `unlink`   | —                          | Unlink Spotify account                 |

_Future: `view` (show linked account), `feed` (play in VC + update)_

---

### **MODERATION Commands** (`moderation.py`) — 34 total

**Cog Name:** Moderation  
**Permission Required:** Manage Messages/Kick/Ban (varies)  
**Status:** ❌ Not implemented

#### User Management

| Command            | Parameters                                                          | Purpose                       |
| ------------------ | ------------------------------------------------------------------- | ----------------------------- |
| `kick`             | `member: discord.Member`, `reason: str \| None`                     | Kick member                   |
| `ban`              | `user: discord.User`, `reason: str \| None`, `delete_days: int = 0` | Ban user                      |
| `unban`            | `user: discord.User`                                                | Unban user                    |
| `ban list`         | —                                                                   | List banned members           |
| `mute`             | `member: discord.Member`, `duration: str \| None`                   | Mute member                   |
| `unmute`           | `member: discord.Member`                                            | Unmute member                 |
| `timeout`          | `member: discord.Member`, `duration: str`                           | Timeout member (max 28 days)  |
| `untimeout`        | `member: discord.Member`                                            | Remove timeout                |
| `nick`             | `member: discord.Member \| None`, `new_nick: str`                   | Change nickname               |
| `nick reset`       | `member: discord.Member \| None`                                    | Reset nickname                |
| `force nick`       | `member: discord.Member`, `new_nick: str`                           | Force change nickname (admin) |
| `force nick reset` | `member: discord.Member`                                            | Force reset nickname (admin)  |
| `nick ban`         | `nickname: str`                                                     | Ban a nickname                |
| `nick unban`       | `nickname: str`                                                     | Unban a nickname              |

#### Mute Types

| Command       | Parameters                                      | Feature                             |
| ------------- | ----------------------------------------------- | ----------------------------------- |
| `imute`       | `member: discord.Member`, `reason: str \| None` | Ignore mute (no images/attachments) |
| `inmute list` | —                                               | List ignored mutes                  |
| `rmute`       | `member: discord.Member`, `role: discord.Role`  | Role-based mute                     |
| `rmute list`  | —                                               | List role mutes                     |
| `picperms`    | `member: discord.Member`                        | Toggle image permissions            |

#### Warning System

| Command      | Parameters                              | Feature               |
| ------------ | --------------------------------------- | --------------------- |
| `warn`       | `member: discord.Member`, `reason: str` | Warn member           |
| `warned`     | `member: discord.Member \| None`        | List member warnings  |
| `clearwarns` | `member: discord.Member`                | Clear member warnings |

#### Channel Management

| Command           | Parameters                             | Feature                     |
| ----------------- | -------------------------------------- | --------------------------- |
| `lock`            | `channel: discord.TextChannel \| None` | Prevent sending messages    |
| `unlock`          | `channel: discord.TextChannel \| None` | Unlock channel              |
| `lockdown`        | —                                      | Lockdown entire server      |
| `unlockdown`      | —                                      | Unlock entire server        |
| `lockdown role`   | `role: discord.Role`                   | Remove role from channel    |
| `unlockdown role` | `role: discord.Role`                   | Restore role access         |
| `slowmode`        | `delay: int`                           | Set slowmode (0 = off)      |
| `hide`            | `channel: discord.TextChannel \| None` | Hide channel from @everyone |
| `unhide`          | `channel: discord.TextChannel \| None` | Unhide channel              |
| `purge`           | `limit: int`                           | Bulk delete messages        |

#### Bot Settings

| Command    | Parameters              | Feature               |
| ---------- | ----------------------- | --------------------- |
| `nickname` | `new_nick: str \| None` | Change bot's nickname |

---

### **ROLES Commands** (`roles.py`) — 22 total

**Cog Name:** Roles  
**Permission Required:** Manage Roles (varies)  
**Status:** ❌ Not implemented

#### Role Info

| Command     | Parameters           | Purpose               |
| ----------- | -------------------- | --------------------- |
| `role list` | —                    | List all server roles |
| `role info` | `role: discord.Role` | Show role info        |

#### Role Management

| Command            | Parameters                                     | Feature                     |
| ------------------ | ---------------------------------------------- | --------------------------- |
| `role add`         | `member: discord.Member`, `role: discord.Role` | Assign role                 |
| `role remove`      | `member: discord.Member`, `role: discord.Role` | Remove role                 |
| `role create`      | `name: str`, `color: str \| None`              | Create new role             |
| `role delete`      | `role: discord.Role`                           | Delete role                 |
| `role clear`       | `member: discord.Member`                       | Remove all roles            |
| `role restore`     | `member: discord.Member`                       | Restore removed roles       |
| `role mass assign` | `role: discord.Role`, `group: str`             | Assign to all/bots/humans   |
| `role mass remove` | `role: discord.Role`, `group: str`             | Remove from all/bots/humans |
| `role mass cancel` | —                                              | Cancel ongoing operation    |

#### Role Customization

| Command            | Parameters                                    | Feature                   |
| ------------------ | --------------------------------------------- | ------------------------- |
| `role color`       | `role: discord.Role`, `color: str`            | Change role color         |
| `role rename`      | `role: discord.Role`, `new_name: str`         | Rename role               |
| `role icon`        | `role: discord.Role`, `icon_url: str \| None` | Set role icon             |
| `role hoist`       | `role: discord.Role`                          | Toggle display separately |
| `role mentionable` | `role: discord.Role`                          | Toggle mentionability     |

#### Permissions

| Command                  | Parameters                        | Feature                                               |
| ------------------------ | --------------------------------- | ----------------------------------------------------- |
| `strip`                  | `role: discord.Role`              | Remove dangerous perms (admin, delete messages, etc.) |
| `fakepermissions add`    | `role: discord.Role`, `perm: str` | Add fake permission                                   |
| `fakepermissions remove` | `role: discord.Role`, `perm: str` | Remove fake permission                                |
| `fakepermissions list`   | `role: discord.Role \| None`      | List fake permissions                                 |
| `fakepermissions reset`  | `role: discord.Role \| None`      | Reset all fake permissions                            |

---

### **SETUP & CONFIG Commands** (`setup.py`) — 29 total

**Cog Name:** Setup  
**Permission Required:** Manage Guild (varies)  
**Status:** ❌ Not implemented

#### Boost Notifications

| Command         | Parameters                     | Feature                        |
| --------------- | ------------------------------ | ------------------------------ |
| `boost channel` | `channel: discord.TextChannel` | Set boost notification channel |
| `boost message` | `message: str`                 | Customize boost message        |
| `boost view`    | —                              | Preview boost notification     |
| `boost remove`  | —                              | Disable boost notifications    |

#### Welcome/Goodbye Messages

| Command           | Parameters                     | Feature                |
| ----------------- | ------------------------------ | ---------------------- |
| `welcome toggle`  | `enabled: bool`                | Enable/disable welcome |
| `welcome channel` | `channel: discord.TextChannel` | Set welcome channel    |
| `welcome message` | `message: str`                 | Set welcome message    |
| `welcome test`    | —                              | Test message           |
| `goodbye toggle`  | `enabled: bool`                | Enable/disable goodbye |
| `goodbye channel` | `channel: discord.TextChannel` | Set goodbye channel    |
| `goodbye message` | `message: str`                 | Set goodbye message    |
| `goodbye test`    | —                              | Test message           |

#### Backups

| Command          | Parameters                       | Feature              |
| ---------------- | -------------------------------- | -------------------- |
| `backup create`  | `name: str \| None`              | Backup server config |
| `backup restore` | `name: str`                      | Restore from backup  |
| `backup list`    | —                                | List all backups     |
| `backup view`    | `name: str`                      | View backup details  |
| `backup delete`  | `name: str`                      | Delete backup        |
| `backup rename`  | `old_name: str`, `new_name: str` | Rename backup        |

#### Channel Management

| Command            | Parameters                                                               | Feature                   |
| ------------------ | ------------------------------------------------------------------------ | ------------------------- |
| `channel create`   | `name: str`, `type: str`, `options: dict`                                | Create text/voice channel |
| `channel delete`   | `channel: discord.abc.GuildChannel`                                      | Delete channel            |
| `channel rename`   | `channel: discord.abc.GuildChannel`, `new_name: str`                     | Rename channel            |
| `channel topic`    | `channel: discord.TextChannel`, `topic: str`                             | Set channel topic         |
| `channel nsfw`     | `channel: discord.TextChannel`, `enabled: bool`                          | Toggle NSFW               |
| `channel category` | `channel: discord.abc.GuildChannel`, `category: discord.CategoryChannel` | Move to category          |

---

### **VOICE Commands** (`voice.py`) — 15 total

**Cog Name:** Voice  
**Features:** VoiceCenter temp channel system  
**Status:** ❌ Not implemented

#### VoiceCenter Setup

| Command          | Parameters                          | Feature                        |
| ---------------- | ----------------------------------- | ------------------------------ |
| `setup channel`  | `channel: discord.VoiceChannel`     | Set join-to-create channel     |
| `setup category` | `category: discord.CategoryChannel` | Category for temp channels     |
| `setup name`     | `name: str`                         | Default name for temp channels |
| `setup bitrate`  | `bitrate: int`                      | Default bitrate (8000-384000)  |
| `setup rolejoin` | `role: discord.Role \| None`        | Role users get on join         |
| `setup panel`    | `channel: discord.TextChannel`      | Post control panel             |
| `cleanup`        | —                                   | Clean empty/stuck channels     |

#### Temp Channel Management

| Command   | Parameters      | Feature              |
| --------- | --------------- | -------------------- |
| `lock`    | —               | Lock voice channel   |
| `unlock`  | —               | Unlock voice channel |
| `limit`   | `limit: int`    | Set user limit       |
| `name`    | `new_name: str` | Rename channel       |
| `bitrate` | `bitrate: int`  | Set bitrate          |
| `info`    | —               | Show channel info    |

#### Access Control

| Command  | Parameters           | Feature                 |
| -------- | -------------------- | ----------------------- |
| `admit`  | `user: discord.User` | Admit to locked channel |
| `reject` | `user: discord.User` | Reject from joining     |
| `ghost`  | —                    | Hide from non-members   |

---

### **FILTERS & PROTECTION Commands** (`filters.py`, `protection.py`) — 10 total (est.)

**Status:** ❌ Not implemented

#### Automod Filters

| Command          | Parameters     | Feature                 |
| ---------------- | -------------- | ----------------------- |
| `link add`       | `pattern: str` | Add link filter (regex) |
| `link remove`    | `pattern: str` | Remove link filter      |
| `link list`      | —              | List link filters       |
| `word add`       | `word: str`    | Add word filter         |
| `word remove`    | `word: str`    | Remove word filter      |
| `word list`      | —              | List word filters       |
| `mention add`    | `word: str`    | Add mention filter      |
| `mention remove` | `word: str`    | Remove mention filter   |
| `caps add`       | `word: str`    | Add caps filter         |
| `caps remove`    | `word: str`    | Remove caps filter      |
| `reset`          | —              | Reset all filters       |

---

### **MUSIC Commands** (`music.py`) — 6 total

**Cog Name:** Music  
**Status:** ❌ Not implemented (Spotify feed alternative)

| Command  | Parameters      | Feature                     |
| -------- | --------------- | --------------------------- |
| `play`   | `query: str`    | Play song (YouTube/Spotify) |
| `pause`  | —               | Pause playback              |
| `skip`   | —               | Skip current track          |
| `queue`  | `page: int = 1` | View song queue             |
| `stop`   | —               | Stop playback & disconnect  |
| `volume` | `level: int`    | Set volume (0-100)          |

---

### **MISCELLANEOUS Commands** (`misc.py`) — 11 total

**Cog Name:** Miscellaneous  
**Features:** Autoresponders, reaction roles, embed builder  
**Status:** ❌ Not implemented

#### Autoresponders

| Command                | Parameters                 | Purpose                    |
| ---------------------- | -------------------------- | -------------------------- |
| `autoresponder add`    | `trigger: str`, `msg: str` | Create auto-reply message  |
| `autoresponder remove` | `trigger: str`             | Delete autoresponder       |
| `autoresponder list`   | —                          | List all autoresponders    |
| `autoresponder edit`   | `trigger: str`, `msg: str` | Edit autoresponder message |

#### Reaction Roles

| Command                | Parameters                         | Purpose                         |
| ---------------------- | ---------------------------------- | ------------------------------- |
| `reactionrole add`     | `emoji: str`, `role: discord.Role` | Add emoji → role binding        |
| `reactionrole remove`  | `emoji: str`                       | Remove reaction role binding    |
| `reactionrole list`    | —                                  | List all reaction role bindings |
| `reactionrole message` | `link or ID`                       | Set/view reaction role message  |

#### Embed Creation

| Command | Parameters                      | Purpose                       |
| ------- | ------------------------------- | ----------------------------- |
| `embed` | `json: str`                     | Create custom embed from JSON |
| `poll`  | `question: str`, `options: str` | Create reaction poll          |

---

### **SETUP Commands** (`setup.py`) — 2 total (Modal-based UI)

**Cog Name:** Setup  
**Features:** Interactive wizard for welcome, jail, mute roles, bot protection  
**Status:** ✅ Fully Implemented (Interactive Modal System)

**Actual Commands:**

- `setup` — Opens interactive server setup wizard (buttons for welcome, jail, mute, bot protection)
- `setup-sync` — Re-applies mute/jail permission overrides to every channel

**UI Sections (via Modal):**

- Welcome: channel, member role, bot role
- Jail: channel, role, create jail role option
- Mutes: setup mute, imute, rmute roles individually
- Bot Protection: toggle bot lock setting

**Note:** This cog uses interactive modals (SetupView, WelcomeView, JailView, MuteView) rather than separate slash commands. Configuration happens through modal buttons/forms, not text commands.

---

### **INFO Commands** (`info.py`) — 17 total

**Cog Name:** Info  
**Features:** User/server/channel info, image processing  
**Status:** ✅ Fully Implemented (11 commands + groups)

**Existing Commands:**

- `serverinfo` (si), `channelinfo` (ci), `userinfo` (ui), `botinfo` (bi)
- `banner` (bn), `avatar` (av), `sbanner` (sbn), `sav`
- `icon` group (ic) with subcommands: set
- `gbanner` group (gbn) with subcommands: set
- `image` group (img) with subcommands: darken, lighten, round

**Note:** All commands fully implemented with image processing and asset management.

---

## 📊 Complete Command Statistics

### By Module

```
✅ CORE (main.py):               16 commands [IMPLEMENTED]
✅ INFO (info.py):               11 commands [IMPLEMENTED]
✅ SETUP (setup.py):              2 commands [IMPLEMENTED - Interactive Modal UI]
✅ MISC (misc.py):               11 commands [IMPLEMENTED]

✅ MODERATION (moderation.py):   34 commands [SCAFFOLDED - ready for testing]
✅ ROLES (roles.py):             22 commands [SCAFFOLDED - ready for testing]
✅ VOICE (voice.py):             15 commands [SCAFFOLDED - ready for testing]
✅ FILTERS (filters.py):         11 commands [SCAFFOLDED - ready for testing]

⚠️ SPOTIFY (spotify.py):          5 commands [PARTIAL - basic structure, needs API]
⚠️ MUSIC (music.py):              6 commands [PARTIAL - needs music library]
```

### Totals

| Metric                     | Count                                     |
| -------------------------- | ----------------------------------------- |
| **Total Commands**         | **133** (actual, not planned)             |
| **Fully Implemented**      | **40** (30%)                              |
| **Scaffolded (Testing)**   | **82** (62%)                              |
| **Partial/Needs Work**     | **11** (8%)                               |
| **Total Cogs**             | **10**                                    |
| **Cogs Fully Implemented** | **4** (main, info, setup, misc)           |
| **Cogs Scaffolded**        | **4** (moderation, roles, voice, filters) |
| **Cogs Partial**           | **2** (spotify, music)                    |

### Implementation Priority

1. **TESTING** — Verify all 82 scaffolded commands work with Discord API
2. **STORAGE** — Replace TODO placeholders with persistent guild storage
3. **EVENT LISTENERS** — Implement on_message, on_reaction_add, on_voice_state_update
4. **MUSIC** (6 cmds) — Complete music player integration
5. **SPOTIFY** (5 cmds) — Integrate Spotify API
6. **DOCUMENTATION** — Update command docstrings with parameters/examples

---

## 🔧 Cog Files to Create

```
cogs/
├── main.py           ✅ DONE (16 core commands)
├── info.py           ✅ DONE (11 commands - full implementation)
├── setup.py          ✅ DONE (2 commands - Interactive Modal UI)
├── misc.py           ✅ DONE (11 commands - autoresponders, reaction roles, embeds)
├── moderation.py     ✅ SCAFFOLDED (34 commands - ready for testing)
├── roles.py          ✅ SCAFFOLDED (22 commands - ready for testing)
├── voice.py          ✅ SCAFFOLDED (15 commands - ready for testing)
├── filters.py        ✅ SCAFFOLDED (11 commands - ready for testing)
├── spotify.py        ⚠️ PARTIAL (5 commands - needs Spotify API)
└── music.py          ⚠️ PARTIAL (6 commands - needs music library)
```

---

## 📋 Commands Implementation Checklist

### ✅ CORE COMMANDS TO IMPLEMENT

#### 1️⃣ **Moderation** (`moderation.py`)

- [ ] `
- [ ] `imute` — Ignore mute (image mute that prevents users from sending images/attachments)
- [ ] `inmute list` — List ignored mutes
- [ ] `rmute` — Role-based mute
- [ ] `rmute list` — List role mutes
- [ ] `warn` — Warn members
- [ ] `warned` — List member warnings in guild
- [ ] `clearwarns` — Clear member warnings
- [ ] `picperms` toggle pic perms for a user (allow or disallow sending images/attachments)
- [ ] `purge` — Bulk delete messages
- [ ] `lock` — Lockdown a channel (prevent sending messages)
- [ ] `unlock` — Unlock a channel
- [ ] `lockdown` - Lockdown entire server (prevent sending messages in all channels)
- [ ] `unlockdown` - Unlock entire server
- [ ] `lockdown role` - Removes a role from accessing the current channel (can be used for more targeted lockdowns like muting a specific role in a channel)
- [ ] `unlockdown role` - Restores a role's access to the current channel
- [ ] `slowmode` — Set slowmode delay {0 for off}
- [ ] `hide` — Hide a channel from everyone except mods/admins
- [ ] `unhide` — Unhide a channel
- [ ] `kick` — Kick members
- [ ] `ban` — Ban members
- [ ] `ban list` — List banned members
- [ ] `unban` — Unban members
- [ ] `mute` — Mute members
- [ ] `unmute` — Unmute members
- [ ] `timeout` — Timeout members
- [ ] `untimeout` — Remove timeout from members
- [ ] `nick` — Change member nickname
- [ ] `nick reset` — Reset member nickname
- [ ] `force nick` — Force change another member's nickname (admin only)
- [ ] `force nick reset` — Force reset another member's nickname (admin only)
- [ ] `nick ban` — Ban a nickname (prevent users from using a specific nickname)
- [ ] `nick unban` — Unban a nickname
- [ ] `nickname` — Change the bot's nickname in the server

#### 2️⃣ **Roles** (`roles.py`)

- [ ] `role list` — List all roles in the server
- [ ] `role info` — Show information about a specific role
- [ ] `role add` — Assign role to member
- [ ] `role remove` — Remove role from member
- [ ] `role create` — Create a new role
- [ ] `role delete` — Delete a role
- [ ] `role color` — Change role color
- [ ] `role rename` — Rename a role
- [ ] `role icon` — Set role icon
- [ ] `role hoist` — Toggle role hoisting
- [ ] `role mentionable` — Toggle role mentionability
- [ ] `role mass assign` — Assign a role to all members or a specific group (e.g., all bots, all humans)
- [ ] `role mass remove` — Remove a role from all members or a specific group
- [ ] `role mass cancel` — Cancel an ongoing mass role assignment/removal operation
- [ ] `role restore` - Restore a members's previously removed roles (e.g., after a mute or timeout expires)
- [ ] `role clear` - Remove all roles from a member
- [ ] `strip` - Remove dangerous permissions from a role (administrator, manage messages, manage channels, etc.)
- [ ] `fakepermissions add` — Add fake permission to role
- [ ] `fakepermissions remove` — Remove fake permission
- [ ] `fakepermissions list` — List fake permissions
- [ ] `fakepermissions reset` — Reset all fake permissions

#### 3️⃣ **Setup & Configuration** (`setup.py`)

    # boost

- [ ] `boost channel` — Set boost notification channel
- [ ] `boost message` — Customize boost notification message
- [ ] `boost view` — Preview boost notification
- [ ] `boost remove` — Remove boost notifications
  # welcome/goodbye
- [ ] `welcome toggle` — Enable/disable welcome messages
- [ ] `welcome test` — Test welcome message
- [ ] `welcome channel` — Set welcome message channel
- [ ] `welcome message` — Set welcome message
- [ ] `goodbye toggle` — Enable/disable goodbye messages
- [ ] `goodbye test` — Test goodbye message
- [ ] `goodbye channel` — Set goodbye message channel
- [ ] `goodbye message` — Set goodbye message
  # backups
- [ ] `create` — Backup server configuration
- [ ] `restore` — Restore server backup
- [ ] `list` — List all backups
- [ ] `view` — View backup details
- [ ] `delete` — Delete a backup
- [ ] `rename` — Rename a backup`
  # channels
- [ ] `channel create` — Create a new text or voice channel with specific settings
- [ ] `channel delete` — Delete a channel
- [ ] `channel rename` — Rename a channel
- [ ] `channel topic` — Set channel topic
- [ ] `channel nsfw` — Toggle NSFW status of a channel
- [ ] `channel category` — Move channel to a category

#### 4️⃣ **Voice** (`voice.py`) Temp voice system created when user joins a join-to-create channel, deleted when empty (VoiceCenter) - join-to-create channel system

- [ ] `setup` - Setup VoiceCenter
  - [ ] `channel` - Set join-to-create channel (bot creates one if not set)
  - [ ] `category` - Set category for temp channels
  - [ ] `name` - Set default name for temp channels
  - [ ] `bitrate` - Set default bitrate for temp channels
  - [ ] `rolejoin` - set a role that users get when join any voice channel
  - [ ] `pannel` - The the channel where the bot posts the pannel with buttons to manage temp channels
- [ ] `cleanup` - Clean up temp channels (delete empty channels, fix channels stuck)
- [ ] `lock` — lock voice channel
- [ ] `unlock` — unlock voice channel
- [ ] `limit` — set user limit
- [ ] `name` — rename voice channel
- [ ] `bitrate` — set bitrate
- [ ] `info` — show channel info
- [ ] `admit` - admit user to locked voice channel (the bot send the channel own in the vc if some tried to join they can either be admitted or rejected by the channel own)
- [ ] `reject` - reject user from joining voice channel (can be used for raids or to kick users from temp channels)
- [ ] `ghost` - make voice channel invisible to everyone except people in it (and mods/admins)

#### 5️⃣ **Filters & Protection** (`filters.py`, `protection.py`)

- [ ] `link` - add/delete/list user puts a link and adds it to discord automod filter as regex
- [ ] `word` - add/delete/list user puts a word and adds it to discord automod filter
- [ ] `mention` - add/delete/list user puts a word and adds it to
- [ ] `caps` - add/delete/list user puts a word and adds it to discord automod filter
- [ ] `reset` - reset all filter settings

#### 6️⃣ **Music** (`music.py`)

- [ ] `play` — Play a song
- [ ] `pause` — Pause playback
- [ ] `skip` — Skip current track
- [ ] `queue` — View song queue
- [ ] `stop` — Stop playback
- [ ] `volume` — Adjust volume

#### 7️⃣ **Spotify** (`spotify.py`) — Already Partially Implemented

- [ ] `link` — Link Spotify account
- [ ] `now` — Show currently playing track control next/playpause/previous
- [ ] `playlist` — Create/manage playlists
- [ ] `search` — Search Spotify
- [ ] `unlink` — Unlink Spotify account
- [ ] `view` — View linked Spotify account
- [ ] `feed` - play track in voice channel and update with currently playing track

#### 8️⃣ **Info** (`info.py`) — Already Implemented

- ✅ General information commands
- ✅ Image/picture commands

### 9️⃣ **Levels**

### 0️⃣ **Miscellaneous**

- [ ] `poll` — Create a reaction poll
- [ ] `embed` — Create a custom embed
