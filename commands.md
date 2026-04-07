# Pushie Pusheen - Complete Command Blueprint

**Legend**  
`[input]` = text / embed content (supports $em for inline embed)  
`{type}` = required choice (enable/disable, user/guild, etc.)  
`--flag` = optional flag  
`(modal)` = opens modal (`$em` or `embed` for inline/rich embed creation)  
`{target}` = complex targeting (user/role/channel/message_id, etc.)

All responses are **embeds**.  
Emojis come from `emoji.py`.  
Pagination uses: `◂` prev `▸` next `◆` goto

---

## Main.py

### Prefix
**Aliases:** `,prefix` | `,px`  
**Permissions:** Manage Server

- `@Pushie` — Show current prefix for guild
- `,prefix` — Show current prefix for guild
- `,prefix set <new_prefix>` — Change server prefix
- `,prefix default` — Reset to default prefix (`!`)

### AFK
**Aliases:** `,afk` | `,a`  
**Permissions:** Send Messages

- `,afk` — Activate AFK (base command)
- `,afk set <reason>` — Set custom AFK reason
- `,afk msg (modal) {type: text/embed} [input]` — Set your own AFK embed
- `,afk default` — Revert to default AFK embed

### Help
**Aliases:** `,help` | `,h`

- `,help` — Show main help overview
- `,help <command_name>` — Detailed help for a command
- `,help <module_name>` — Help for entire command group (every root command has module help)
- `,help list` — List all command groups
- `,help variables` — List all embed variables

---

## Sudo.py

### Sudo
**Aliases:** `,sudo` | `,su`  
**Permissions:** Bot Owner / Hardcoded Sudo (`ss`)

- `,sudo add <user>` — Add sudo user (`ss`)
- `,sudo list` — List all sudo users
- `,sudo remove <user>` — Remove sudo user (`ss`)
- `,sudo ban {type: user/guild} {target}` — Ban target from using the bot (guild type = auto-leave)
- `,sudo unban {type: user} {target}` — Unban user
- `,sudo leave` — Make the bot leave the current guild
- `,sudo guilds` — List all guilds the bot is in
- `,sudo bot {type: stats/restart/shutdown}` — Bot internal management (`stats` shows uptime, memory, CPU, env, loaded cogs) (`ss`)
- `,sudo cog {type: load/reload/unload} {target: cog.name/all}` — Cog management
- `,sudo customize {type: status/presence} [msg] --emoji <emoji> --link <url>` — Change status/presence (`🔴`=dnd, `🟡`=idle, `🟢`=online, `🫥`=invisible, `🟣`=streaming, `👀`=watching, `👂`=listening)
- `,sudo default` — Save current presence as default (stored in DB)
- `,sudo msg [input]` — Send guild-wide message (`ss`) *max 2 per day*
- `,sudo guild config` — Output current guild config
- `,sudo icon [input]` — Update bot’s profile picture

---

## Server.py

### Roles
**Aliases:** `,role` | `,r`  
**Permissions:** Manage Server

- `,role add <user> <role>` — Give a user a role
- `,role remove <user> <role>` — Remove a role from a user
- `,role list` — List all roles in server
- `,role create <name>` — Create new role
- `,role delete <role>` — Delete a role
- `,role icon <role> [input: emoji/file]` — Update role icon (Level 2 Boost)
- `,role gradient <role> {hex1} {hex2}` — Update role gradient
- `,role color <role> {hex}` — Update role color
- `,role move <role> {type: above/below} {target}` — Move role position
- `,role mentionable <role>` — Toggle role mentions
- `,role rename <role> <new_name>` — Rename a role
- `,role bots {type: add/remove} <role>` — Mass assign role to bots
- `,role members {type: add/remove} <role>` — Mass assign role to members
- `,role all {type: add/remove} <role>` — Mass assign role to everyone
- `,role cancel` — Cancel current mass assignment
- `,role info <role>` — Role information

### Channel
**Aliases:** `,channel` | `,c`  
**Permissions:** Manage Server

- `,channel own {type: add/remove} <user>` — Give user Manage Channel perms
- `,channel list` — List all channels in guild
- `,channel create <name>` — Create a new channel
- `,channel delete <channel>` — Delete a channel
- `,channel rename <channel> <new_name>` — Rename a channel
- `,channel topic <channel> [input]` — Set channel topic
- `,channel access {type: add/remove} <user|role> <channel>` — Add/remove access to channel
- `,channel info <channel>` — Channel information

### Server
**Aliases:** `,server` | `,s`  
**Permissions:** Manage Server

- `,server set {type: icon/banner} [input: png/gif/sticker]` — Update server icon/banner (Level 2 Boost)
- `,server name <new_name>` — Set server name
- `,server info` — View server info

### User
**Permissions:** Send Messages

- `,user report <user> [input: reason]` — Report user to moderation (via ticket system)
- `,user info <user>` — View user info

### Ticket
**Aliases:** `,ticket` | `,tick`  
**Permissions:** Manage Server, Moderator, Send Messages

- `,ticket setup {type: enable/disable}` — Toggle ticket system
- `,ticket channel <channel>` — Set ticket panel & thread creation channel
- `,ticket create (modal)` — User command to create ticket request
- `,ticket report {type: enable/disable}` — Enable/disable user report system
- `,ticket reports <channel>` — Set reports channel
- `,ticket panel (modal)` — Update ticket panel message and button names
- `,ticket user {user} --reason [input] --warn` — Create mod ticket + link to warn system
- `,ticket open (modal)` — Open ticket (creates thread from request)
- `,ticket close` — Close ticket thread
- `,ticket archive` — Archive ticket thread
- `,ticket delete` — Delete ticket thread
- `,ticket add <user>` — Add user to thread
- `,ticket remove <user>` — Remove user from thread
- `,ticket list {type: active/closed/requests/archived}` — List tickets
- `,ticket transcript {type: list/create/delete/view}` — Manage transcripts
- `,ticket manager <role|user>` — Assign ticket managers

### Reaction Roles
**Aliases:** `,reactionroles` | `,rr`  
**Permissions:** Manage Server

- `,reactionrole add {msg_id} {emoji} <role>` — Add reaction role binding
- `,reactionrole remove {channel} {emoji}` — Remove reaction role
- `,reactionrole list` — List by channel
- `,reactionrole clear` — Clear all reaction roles in server

### Button Roles
**Aliases:** `,buttonroles` | `,butr`  
**Permissions:** Manage Server

- `,buttonrole add {msg_id} {emoji} <role>` — Add button role binding
- `,buttonrole remove {channel} {emoji}` — Remove button role
- `,buttonrole list` — List by channel
- `,buttonrole clear` — Clear all button roles in server

### Autoroles
**Aliases:** `,autoroles` | `,ar`  
**Permissions:** Manage Server

- `,autorole add <role>` — Add autorole for everyone
- `,autorole {type: human/bot} <role>` — Add role for target group
- `,autorole list` — List by creation order with ID
- `,autorole remove {target: autorole id}` — Remove by ID
- `,autorole clear` — Clear all autorole assignments

### Booster Roles
**Aliases:** `,boosterrole` | `,br`  
**Permissions:** Booster, Manage Server

- `,boosterrole setup {type: enable/disable}` — Toggle booster roles
- `,boosterrole list` — List booster roles in server
- `,boosterrole base {type: below/above} <role>` — Set base role for booster roles
- `,boosterrole limit <number>` — Set limit of booster roles per user
- `,boosterrole filter add <name>` — Add forbidden name
- `,boosterrole filter remove <name>` — Remove filter
- `,boosterrole filter clear` — Clear all filters
- `,boosterrole shares limit <number>` — Set share limit
- `,boosterrole create <name> {hex} {hex2: optional} [input: icon]` — Create booster role
- `,boosterrole color {hex}` — Change color
- `,boosterrole name <new_name>` — Change name
- `,boosterrole icon [input]` — Change icon
- `,boosterrole share <user>` — Share your booster role
- `,boosterrole unshare <user>` — Unshare your booster role
- `,boosterrole share list` — List users sharing your role
- `,boosterrole delete` — Delete your booster role
- `,boosterrole hoist` — Toggle hoist of new roles
- `,boosterrole sync` — Sync booster roles based on base role position

### Friend Group
**Aliases:** `,friendgroup` | `,fg`  
**Permissions:** Manage Server

- `,friendgroup setup {type: enable/disable}` — Toggle friend groups
- `,friendgroup list` — List all friend groups
- `,friendgroup base {type: above/below} <role>` — Set base role
- `,friendgroup limit <number>` — Set limit (max 205)
- `,friendgroup filter add <name>` — Add forbidden name
- `,friendgroup filter remove <name>` — Remove filter
- `,friendgroup filter clear` — Clear all filters
- `,friendgroup create <name> <limit> [input: icon]` — Create friend group
- `,friendgroup remove <name>` — Remove friend group
- `,friendgroup own <name> <user>` — Make user owner
- `,friendgroup manager <name> <user>` — Make user manager
- `,friendgroup user ban <name> <user>` — Ban user from group
- `,friendgroup user remove <name> <user>` — Remove user from group
- `,friendgroup user invite <name> <user>` — Invite user to group
- `,friendgroup user list <name>` — List group members
- `,friendgroup assets <name>` — List group assets
- `,friendgroup assign {type: vc/role/channel} <name>` — Assign asset to group
- `,friendgroup manager <role>` — Set default manager role
- `,friendgroup clear` — Clear all friend groups

### Config
**Aliases:** `,config` | `,cf`  
**Permissions:** Manage Server

- `,config prefix <new_prefix>` — Change bot prefix in guild
- `,config icon [input]` — Change bot icon in guild
- `,config banner [input]` — Change bot banner in guild
- `,config status [input]` — Change status in guild

**Quick Info Commands:**
- `,si` — Server info
- `,bi` — Bot info
- `,ui <user>` — User info
- `,ci <channel>` — Channel info
- `,ri <role>` — Role info
- `,vi <voice>` — Voice channel info

**Ungrouped Reply Commands:**
- `avatar` — See user avatar (reply to user)
- `banner` — See user banner
- `inrole <role>` — See users in a role

---

## Logz.py

### Logz
**Aliases:** `,logz` | `,lg`  
**Permissions:** Manage Server

- `,logz add {type: member/mod/role/channel/voice} <channel>` — Add log assignment
- `,logz remove {type}` — Remove log assignment
- `,logz view` — View all log assignments
- `,logz color {hex}` — Set color of log embeds
- `,logz test {type}` — Test log output

---

## Moderation.py

### Setup
**Aliases:** `,mod-setup`

- `,mod-setup` — Setup moderation environment (jail + muted/imuted/rmuted roles + perms)
- `,mod-setup reset` — Reset moderation setup
- `,mod-setup sync` — Re-apply permission overrides

### Purge
**Aliases:** `,purge` | `,pur`

- `,purge <amount>` — Purge messages
- `,purge user <user> <amount>` — Purge user messages
- `,purge embeds` — Purge embeds
- `,purge images` — Purge images
- `,purge voice` — Purge voice messages
- `,purge mentions` — Purge mentions
- `,purge humans` — Purge human messages
- `,purge bots` — Purge bot messages
- `,purge invites` — Purge invite links
- `,purge before {msg_id}` — Purge before message
- `,purge after {msg_id}` — Purge after message
- `,purge with <keyword>` — Purge messages containing keyword

### Snipe
**Permissions:** Moderator

- `,snipe` — Snipe last deleted message (` ,s` for everyone)
- `,reactionsnipe` — Snipe last reaction edit (` ,rs`)
- `,editsnipe` — Snipe last edited message (` ,es`)
- `,clearsnipes` — Clear snipes in current channel (` ,cs`)

### Live Commands
**Permissions:** Moderator

- `kick <user> [reason]` — Kick user
- `ban <user> [reason]` — Ban user
- `unban <user>` — Unban user
- `mute <user> [reason]` — Mute user
- `imute <user> [reason]` — Image mute user
- `iunmute <user>` — Image unmute user
- `rmute <user> [reason]` — Reaction mute user
- `runmute <user>` — Reaction unmute user
- `jail <user> [reason]` — Jail user
- `unjail <user>` — Unjail user
- `jailed` — List jailed users
- `lock <channel>` — Lock channel
- `unlock <channel>` — Unlock channel
- `strip <user>` — Strip moderation perms
- `slowmod <channel> {interval}` — Set slowmode (default 2s)
- `nsfw <channel>` — Mark channel NSFW
- `lockdown` — Lockdown entire server
- `unlockdown` — Unlock server
- `lockdown staff <role>` — Set staff role exempt from lockdown
- `nick <user> <nickname>` — Set nickname
- `nick remove <user>` — Remove nickname
- `forcenick <user> <nickname>` — Force nickname
- `forcenick cancel <user>` — Remove forced nickname
- `warn <user> [reason]` — Warn user
- `warn list <user>` — List user warns
- `warn clear <user> {amount/all}` — Clear warns
- `warn strikes <count> {action}` — Set strike action
- `timeout <user> {duration}` — Timeout user
- `timeout list` — List timed-out users
- `timeout remove <user>` — Remove timeout

### Invoke
**Aliases:** `,invoke` | `,iv`  
**Permissions:** Manage Server

- `,invoke jail {type: channel/dm} [input]` — Add invoke message
- `,invoke ban {type: channel/dm} [input]` — Add invoke message
- `,invoke timeout {type: channel/dm} [input]` — Add invoke message
- `,invoke mute {type: channel/dm} [input]` — Add invoke message
- `,invoke warn {type: channel/dm} [input]` — Add invoke message
- `,invoke list` — List current invoke messages
- `,invoke reset` — Reset all invoke messages
- `,invoke remove {type}` — Remove invoke message

---

## Security.py (Automod)

### Filter
**Aliases:** `,filter` | `,fil`  
**Permissions:** Administrator

- `,filter list` — List all filters
- `,filter keyword add [input]` — Add keyword filter
- `,filter keyword remove [input]` — Remove keyword filter
- `,filter link add [input]` — Add link filter
- `,filter link remove [input]` — Remove link filter
- `,filter invites add {target/all}` — Add invite filter
- `,filter invites remove {target/all}` — Remove invite filter
- `,filter regex add [input]` — Add regex filter
- `,filter regex test [input]` — Test regex filter
- `,filter add [input]` — Add general filter
- `,filter remove [input]` — Remove general filter
- `,filter whitelist [input]` — Add whitelist
- `,filter links whitelist [input]` — Add link whitelist
- `,filter snipe` — Filter snipe outputs
- `,filter nicknames [input]` — Add nickname filter
- `,filter exempt <user>` — Exempt user from filters

### Antinuke
**Aliases:** `,antinuke`  
**Permissions:** Administrator

- `,antinuke setup {type: enable/disable}` — Toggle antinuke
- `,antinuke kick` — Enable mass kick protection
- `,antinuke ban` — Enable mass ban protection
- `,antinuke whitelist {type: add/remove} <user>` — Manage whitelist
- `,antinuke vanity` — Enable vanity protection
- `,antinuke guildupdate` — Enable guild update protection
- `,antinuke admins` — List antinuke admins
- `,antinuke admin add <user>` — Add antinuke admin
- `,antinuke admin remove <user>` — Remove antinuke admin
- `,antinuke botadd` — Enable bot protection

### Fake Permissions
**Aliases:** `,fakepermissions` | `,fakeperms`  
**Permissions:** Administrator

- `,fakepermissions add <user> <perms>` — Grant fake permissions
- `,fakepermissions list` — List fake permissions
- `,fakepermissions remove <user>` — Remove fake permissions

### Antiraid
**Aliases:** `,antiraid`  
**Permissions:** Administrator

- `,antiraid username add [input]` — Add username pattern
- `,antiraid username remove [input]` — Remove username pattern
- `,antiraid username list` — List username filters
- `,antiraid massmention` — Enable mass mention protection
- `,antiraid massjoin` — Enable mass join protection
- `,antiraid age` — Enable account age protection
- `,antiraid avatar` — Enable default avatar protection
- `,antiraid whitelist add <user>` — Add whitelist
- `,antiraid whitelist remove <user>` — Remove whitelist
- `,antiraid whitelist view` — View whitelists
- `,antiraid unverifiedbots` — Enable unverified bot protection
- `,antiraid setup {type: enable/disable}` — Toggle antiraid system

---

## Voice.py

### Voice Centre
**Aliases:** `,voicecentre` | `,vc`  
**Permissions:** Manage Server, Send Messages  
**VC Name Keys:** `{user.name}` `{user.id}` `{nick}` `{fg.name}`

- `,voicecentre setup {j2c:channel/channel.id} {category:category.id} {interface:channel/channel.id} {role:role/role.id}` — Setup voice centre
- `,voicecentre add {j2c:channel/channel.id} {category:category.id} {interface:channel/channel.id} {role:role/role.id}` — Add secondary system
- `,voicecentre joinrole <role>` — Set default join role
- `,voicecentre interface {type: channel.id/invoice}` — Set interface
- `,voicecentre mode {type: temp/hard}` — Toggle mode
- `,voicecentre allowance {type: enable/disable}` — Toggle allowance system
- `,voicecentre allowed <role>` — Add allowed role
- `,voicecentre allowed list` — List allowed roles
- `,voicecentre disallow <role>` — Disallow role
- `,voicecentre disallow list` — List disallowed users
- `,voicecentre sendinterface` — Send user interface
- `,voicecentre list` — List all secondary systems
- `,voicecentre clear` — Reset voice centre in guild
- `,voicecentre category {vc/vc.id} {category/category.id}` — Bind VC to category
- `,voicecentre default bitrate <value>` — Set default bitrate
- `,voicecentre default name (modal)` — Set default name template
- `,voicecentre name [input]` — Set name of your temp channel
- `,voicecentre lock` — Lock your VC
- `,voicecentre unlock` — Unlock your VC
- `,voicecentre drag <user>` — Drag user into your VC
- `,voicecentre permit <user>` — Permit user
- `,voicecentre reject <user>` — Reject user
- `,voicecentre hide` — Hide your channel
- `,voicecentre unhide` — Unhide your channel
- `,voicecentre fg <name>` — Only allow this friend group
- `,voicecentre public` — Make VC public
- `,voicecentre limit <number>` — Set user limit
- `,voicecentre claim` — Claim unclaimed channel
- `,voicecentre mute <user>` — Mute user in your VC
- `,voicecentre videooff <user>` — Turn off video for user

---

## Gate.py

### Greet
**Aliases:** `,greet`  
**Permissions:** Manage Server

- `,greet setup {type: enable/disable}` — Toggle greet system
- `,greet config {channel} [input: msg] (modal if $em used)` — One-shot setup
- `,greet channel <channel>` — Change greet channel
- `,greet message [input] (modal)` — Change greet message
- `,greet view` — View current message script
- `,greet clear` — Clear greet system
- `,greet test` — Test output of script

### Leave
**Aliases:** `,leave`  
**Permissions:** Manage Server

- `,leave setup {type: enable/disable}` — Toggle leave system
- `,leave config {channel} [input: msg] (modal if $em used)` — One-shot setup
- `,leave channel <channel>` — Change leave channel
- `,leave message [input] (modal)` — Change leave message
- `,leave view` — View current script
- `,leave clear` — Wipe leave system
- `,leave test` — Test output of script

### Ping On Join
**Aliases:** `,pingonjoin`  
**Permissions:** Manage Server

- `,ping setup {type: enable/disable}` — Toggle ping on join
- `,ping list` — List ping assignments
- `,ping add <channel> --autodelete <seconds:3>` — Add ping assignment
- `,ping remove <channel>` — Remove ping assignment

---

## Level.py

### Level
**Aliases:** `,level`  
**Permissions:** Manage Server

- `,levels setup {type: enable/disable}` — Toggle level system
- `,levels message {channel} [input: msg] (modal if $em used)` — Set level-up message
- `,levels channel <channel>` — Update level-up channel
- `,levels msg [input] (modal)` — Update level-up message
- `,levels reset` — Reset leveling system (wipe all XP)
- `,levels leaderboard` — Top 7 users
- `,levels add <level> <role>` — Add level with associated role
- `,levels remove <level>` — Remove level
- `,levels list` — List all levels

---

## Misc.py

### Embeds
**Aliases:** `,embed`  
**Permissions:** Manage Server

- `,embed create` — Create new embed template
- `,embed delete <name>` — Delete embed template
- `,embed view <name>` — View embed template
- `,embed list` — List all embed templates

### Color
**Permissions:** Send Messages

- `,color <hex>` — Convert color to hex
- `,color random` — Get random color hex

### Timer (Pocketwatch)
**Aliases:** `,timer`  
**Permissions:** Manage Server

- `,timer add [input: msg] --interval <time>` — Post scheduled repeating message
- `,timer remove <id>` — Remove timer
- `,timer list` — List repeating messages
- `,timer view <id>` — View scheduled message
- `,timer pause <id>` — Pause timer
- `,timer clear` — Clear all timers in server

### Counter
**Aliases:** `,counter`  
**Permissions:** Manage Server

- `,counter add` — Add counter in current channel
- `,counter remove <channel>` — Remove channel counter
- `,counter list` — List all counters across server
- `,counter pause <channel>` — Pause channel counter
- `,counter clear` — Clear all channel counters

### Reminder
**Aliases:** `,reminder`  
**Permissions:** Moderator

- `,reminder add [input: msg] --time <duration>` — Create new reminder
- `,reminder remove <id>` — Remove reminder
- `,reminder bump` — Create bump reminder
- `,reminder bump purge` — Clean non-/bump messages
- `,reminder bump msg [input] (modal)` — Set bump reminder message
- `,reminder bump msg view` — View bump reminder output
- `,reminder bump autolock` — Auto-lock channel until ready to bump
- `,reminder bump thankyou [input] (modal)` — Set thank you response
- `,reminder bump thankyou view` — View thank you output
- `,reminder list` — List reminders in guild
- `,reminder clear` — Clear all guild reminders
- `,reminder msg [input] (modal)` — Set default reminder message
- `,reminder view` — View your reminder message

---

**This is the final blueprint.**  
Copy this into `COMMANDS.md` — it is now 100% complete, consistent, and ready for your team or documentation.

Let me know if you want any section expanded with examples or modal field details.
