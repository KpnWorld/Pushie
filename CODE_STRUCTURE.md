# Pushie Pusheen - Code Structure Overview

**Bot Type:** Purely Prefix Commands (no slash or hybrid commands)  
**Total Commands:** 100+ across 7 cogs  
**Last Updated:** April 07, 2026

---
```
## Directory Structure
Pushie/
├── main.py                  # Bot Entry Point
├── storage.py               # Data layer (GuildData + StorageManager)
├── ui.py                    # UI components & embed factory
├── emojis.py                # Central emoji registry (never hardcoded)
├── requirements.txt         # Dependencies
├── .env.example             # Config template
├── code-structure.md        # This file
│
├── cogs/                    # 7 command cogs (100+ commands)
│ ├── protection.py          # Content filtering (AutoMod)
│ │                         # Groups: ,filter ,fakeperms ,antiraid
│ │                         # Aliases: ,fil ,fkpr ,anti
│ ├── moderation.py          # User enforcement & channel management
│ │                         # Groups: ,purge ,lockdown ,snipe + ungrouped
│ │                         # Aliases: ,lckdn ,pur
│ ├── server.py              # Server Management
│ │                         # Groups: ,role ,channel ,server ,ticket ,level
│ │                         # ,boosterrole ,reactionrole ,buttonrole ,friendgroup
│ │                         # Aliases: ,r ,ch ,ser ,tik ,lev ,br ,rr ,fg
│ ├── misc.py                # Utilities (embeds, color, timer, counter, reminder)
│ ├── info.py                # Information commands & image processing
│ ├── voice.py               # VoiceCentre (temp voice channels)
│ │                         # Group: ,voicecentre
│ │                         # Alias: ,vc
│ ├── logz.py                # Logging system
│ │                         # Group: ,logz
│ │                         # Alias: ,lg
│ ├── gate.py                # Welcome/Leave/Boosting System
│ │                         # Groups: ,greet ,leave ,boost ,test
│ └── setup.py               # Interactive server setup wizard
│                           # Commands: ,setup ,backup
│
├── data/                    # Persistent storage
│ ├── global.json            # Sudo users, banned guilds/users
│ └── guilds/
│     ├── {guild_id}.json    # Per-guild configuration
│     └── ...
│
└── docs/                    # Discord.py reference files (13 files)
├── slashcmds.txt
├── hybridcmds.txt
├── views.txt
├── embeds.txt
├── checks.txt
├── converters.txt
├── cogs.txt
├── errorhandle.txt
├── context.txt
├── audioplayback.txt
├── baisic.txt
├── componentsv2.txt
└── markdown.txt
```

## Code Organization Patterns

### 1. Storage Layer (`storage.py`)
**Pattern:** Dataclass + Manager with caching & locking

```python
@dataclass
class GuildData:
    id: int
    prefix: str = "!"
    mute_role: int | None = None
    jail_channel: int | None = None
    # ... 20+ more fields (voicecentre, autoroles, logs, etc.)

class StorageManager:
    async def get_guild(guild_id: int) -> GuildData
    async def save_guild(guild: GuildData) -> None
    async def set_prefix(guild_id: int, prefix: str) -> None
    # 15+ convenience methods
Thread Safety:

Per-guild asyncio.Lock
Global lock for global.json
Cache-first strategy


2. Command Layer (cogs/)
Pattern: Pure Prefix Commands (no hybrid)
Pythonclass ModCog(commands.Cog):
    @commands.command(name="kick", aliases=["k"])
    @commands.has_guild_permissions(kick_members=True)
    async def kick_user(self, ctx: PushieContext, user: discord.User, *, reason: str = None):
        await ctx.ok(f"Kicked {user.mention}")
Command Types:

All commands are prefix-only
Groups use @commands.group()
No slash commands


3. UI Layer (ui.py)
Pattern: Static factory + BaseView
Pythonclass UI:
    @staticmethod
    def success(msg: str) -> discord.Embed   # ☑️ Green
    @staticmethod
    def error(msg: str) -> discord.Embed     # ❌ Red
    @staticmethod
    def warning(msg: str) -> discord.Embed   # ⚠️ Yellow
    @staticmethod
    def info(msg: str) -> discord.Embed      # ℹ️ Blue

class BaseView(discord.ui.View):
    async def interaction_check(self, interaction)  # Owner-only
    async def on_error(self, interaction, error)    # Clean error display
    async def on_timeout(self)                      # Auto-disable
Standard Format:

Every response: > \emoji` message`
Consistent color: 0xFAB9EC
All buttons/selects use named emojis from emoji.py


4. Bot Initialization (main.py)
Startup Sequence:

Load .env
Setup logging (INFO level)
Create Pushie bot instance
Register global checks (banned guild/user)
Register core commands (ping, afk, help, prefix, sudo)
Load all cogs from cogs/ directory
Connect to Discord

Key Events:

on_ready() — Log status, set presence
on_guild_join() — Welcome message + ban check
on_message() — AFK system, prefix handling, global checks
on_command_error() — Unified error handling


Data Flow Example: Setting a Prefix
textUser → !prefix set !
      ↓
main.py: prefix_cmd()
      ↓
storage.py: set_prefix(guild_id, "!")
      ↓
GuildData.prefix = "!"
      ↓
save_guild() → JSON write (locked)
      ↓
UI.success("Prefix changed to `!`")
      ↓
Discord Embed Response

Error Handling Architecture
Global Checks (in main.py):
Python@bot.check
async def global_banned_guild(ctx):
    return not bot.storage.is_banned_guild(ctx.guild.id)
Command Decorators:

@is_sudo()
@is_guild_admin()
@is_mod()
@guild_only()

Global Error Handler:
Handles 10+ error types with clean embeds.

Important Classes & Methods
StorageManager (Critical)

load_all()
get_guild(guild_id)
save_guild(guild)
set_prefix(), set_afk(), update_setup(), etc.

PushieContext (Custom)
Pythonclass PushieContext(commands.Context):
    async def ok(self, msg: str)      # Green success
    async def err(self, msg: str)     # Red error
    async def warn(self, msg: str)    # Yellow warning
    async def info(self, msg: str)    # Blue info
Permission Decorators

@is_sudo()
@is_guild_owner()
@is_guild_admin()
@is_mod()
@is_boosting()
@guild_only()
@in_voice()


Command Summary
Total Commands: 100+
Cogs: 7
Purely Prefix: All commands use custom prefix or ! (no slash commands)

Technology Stack

discord.py 2.x — Bot framework
aiohttp — Async HTTP
python-dotenv — Config
psutil — Performance monitoring
Flask — Health check endpoint (port 5000)

Architecture Patterns:

100% async
Cog-based modularity
JSON persistence with file locking
Dataclass models
Decorator-based permissions
Factory UI pattern


Status: 🟢 Fully Ready for Production

Before going into it must read commands.txt
and current code strcutre you cannot stop until everything adress in the files are created succesfully with not errors 
