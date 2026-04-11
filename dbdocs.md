# Supabase Setup Guide

This guide will help you set up Supabase for the Pushie bot's database storage.

## Prerequisites

1. Go to [supabase.com](https://supabase.com) and create a free account
2. Create a new project (name it something like "pushie-bot")

## Step 1: Get Your Credentials

1. In your Supabase project dashboard, go to **Settings** > **API**
2. Copy:
   - **Project URL** → This is your `SUPABASE_URL`
   - **Project API Key** (anon/public key is fine) → This is your `SUPABASE_KEY`
3. Add these to your `.env` file:
   ```
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your_anon_key_here
   ```

## Step 2: Create Database Tables

Run these SQL queries in the Supabase SQL Editor:

### Guild Data Table

```sql
CREATE TABLE guild_data (
  id BIGINT PRIMARY KEY,
  data JSONB NOT NULL DEFAULT '{}',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Auto-update the updated_at timestamp
CREATE TRIGGER update_guild_data_timestamp
BEFORE UPDATE ON guild_data
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
```

### Global Data Table

```sql
CREATE TABLE global_data (
  id INT PRIMARY KEY DEFAULT 1,
  data JSONB NOT NULL DEFAULT '{}',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Auto-update the updated_at timestamp
CREATE TRIGGER update_global_data_timestamp
BEFORE UPDATE ON global_data
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
```

### Updated At Trigger Function (if it doesn't exist)

```sql
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

## Step 3: Test Connection

Install the updated dependencies:

```bash
pip install -r requirements.txt
```

The bot will automatically:

1. Connect to Supabase on startup
2. Load all existing guild data
3. Create new guild entries as needed
4. Save changes in real-time

## Migration from File-Based Storage

If you have existing data in the `data/` folder, you can migrate it:

```python
import json
from pathlib import Path
async def migrate_existing_data():
    from storage import StorageManager
    from supabase_client import get_client

    storage = StorageManager()
    client = await get_client()

    # Migrate guild data
    for guild_file in Path("data/guilds").glob("*.json"):
        guild_id = int(guild_file.stem)
        data = json.loads(guild_file.read_text())
        await client.table("guild_data").insert({
            "id": guild_id,
            "data": data
        }).execute()

    # Migrate global data
    global_file = Path("data/global.json")
    if global_file.exists():
        data = json.loads(global_file.read_text())
        await client.table("global_data").insert({
            "id": 1,
            "data": data
        }).execute()
```

## Notes

- All data is stored as JSONB in Supabase, maintaining the same structure
- The bot still caches guild data in memory for performance
- Changes are persisted to the database automatically
- The `get_guild_sync()` method returns cached data (non-blocking)
- Use `get_guild()` for guaranteed fresh data from the database

## Full Schematics
>>> Note: We are not using json anymore so the /data dir will be removed.
>>> We are now using supabase api now here is the schema in supabase
```sql
-- WARNING: This schema is for context only and is not meant to be run.
-- Table order and constraints may not be valid for execution.

CREATE TABLE public.afk (
  user_id bigint NOT NULL,
  guild_id bigint NOT NULL,
  status text,
  set_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT afk_pkey PRIMARY KEY (user_id, guild_id)
);
CREATE TABLE public.antinuke_admins (
  guild_id bigint NOT NULL,
  user_id bigint NOT NULL,
  CONSTRAINT antinuke_admins_pkey PRIMARY KEY (guild_id, user_id)
);
CREATE TABLE public.antinuke_config (
  guild_id bigint NOT NULL,
  enabled boolean NOT NULL DEFAULT false,
  kick_protection boolean NOT NULL DEFAULT false,
  ban_protection boolean NOT NULL DEFAULT false,
  vanity_protection boolean NOT NULL DEFAULT false,
  guild_update boolean NOT NULL DEFAULT false,
  bot_add boolean NOT NULL DEFAULT false,
  CONSTRAINT antinuke_config_pkey PRIMARY KEY (guild_id)
);
CREATE TABLE public.antinuke_whitelist (
  guild_id bigint NOT NULL,
  user_id bigint NOT NULL,
  CONSTRAINT antinuke_whitelist_pkey PRIMARY KEY (guild_id, user_id)
);
CREATE TABLE public.antiraid_config (
  guild_id bigint NOT NULL,
  enabled boolean NOT NULL DEFAULT false,
  massmention boolean NOT NULL DEFAULT false,
  massjoin boolean NOT NULL DEFAULT false,
  age_protection boolean NOT NULL DEFAULT false,
  avatar_protection boolean NOT NULL DEFAULT false,
  unverified_bots boolean NOT NULL DEFAULT false,
  CONSTRAINT antiraid_config_pkey PRIMARY KEY (guild_id)
);
CREATE TABLE public.antiraid_username_patterns (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  guild_id bigint NOT NULL,
  pattern text NOT NULL,
  CONSTRAINT antiraid_username_patterns_pkey PRIMARY KEY (id)
);
CREATE TABLE public.antiraid_whitelist (
  guild_id bigint NOT NULL,
  user_id bigint NOT NULL,
  CONSTRAINT antiraid_whitelist_pkey PRIMARY KEY (guild_id, user_id)
);
CREATE TABLE public.autoresponder_exclusives (
  id bigint NOT NULL DEFAULT nextval('autoresponder_exclusives_id_seq'::regclass),
  guild_id bigint NOT NULL,
  trigger text NOT NULL,
  target_id bigint NOT NULL,
  target_type text NOT NULL CHECK (target_type = ANY (ARRAY['channel'::text, 'role'::text])),
  CONSTRAINT autoresponder_exclusives_pkey PRIMARY KEY (id)
);
CREATE TABLE public.autoresponder_roles (
  id bigint NOT NULL DEFAULT nextval('autoresponder_roles_id_seq'::regclass),
  guild_id bigint NOT NULL,
  trigger text NOT NULL,
  role_id bigint NOT NULL,
  action text NOT NULL CHECK (action = ANY (ARRAY['add'::text, 'remove'::text])),
  CONSTRAINT autoresponder_roles_pkey PRIMARY KEY (id)
);
CREATE TABLE public.autoresponders (
  id bigint NOT NULL DEFAULT nextval('autoresponders_id_seq'::regclass),
  guild_id bigint NOT NULL,
  trigger text NOT NULL,
  response text NOT NULL,
  owner_id bigint NOT NULL,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT autoresponders_pkey PRIMARY KEY (id)
);
CREATE TABLE public.autoroles (
  id bigint NOT NULL DEFAULT nextval('autoroles_id_seq'::regclass),
  guild_id bigint NOT NULL,
  role_id bigint NOT NULL,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  target_type text NOT NULL DEFAULT 'all'::text CHECK (target_type = ANY (ARRAY['all'::text, 'human'::text, 'bot'::text])),
  CONSTRAINT autoroles_pkey PRIMARY KEY (id)
);
CREATE TABLE public.birthday_config (
  guild_id bigint NOT NULL,
  role_id bigint,
  channel_id bigint,
  message text,
  locked boolean DEFAULT false,
  celebrate_roles ARRAY DEFAULT '{}'::bigint[],
  CONSTRAINT birthday_config_pkey PRIMARY KEY (guild_id)
);
CREATE TABLE public.birthdays (
  user_id bigint NOT NULL,
  birthday date NOT NULL,
  set_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT birthdays_pkey PRIMARY KEY (user_id)
);
CREATE TABLE public.boost_messages (
  id bigint NOT NULL DEFAULT nextval('boost_messages_id_seq'::regclass),
  guild_id bigint NOT NULL,
  channel_id bigint NOT NULL,
  message text NOT NULL,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT boost_messages_pkey PRIMARY KEY (id)
);
CREATE TABLE public.booster_role_config (
  guild_id bigint NOT NULL,
  base_role_id bigint,
  role_limit integer DEFAULT 1,
  share_limit integer DEFAULT 5,
  share_max integer DEFAULT 3,
  award_role_id bigint,
  blacklisted_words ARRAY DEFAULT '{}'::text[],
  enabled boolean NOT NULL DEFAULT false,
  base_position text NOT NULL DEFAULT 'below'::text CHECK (base_position = ANY (ARRAY['above'::text, 'below'::text])),
  hoist_new boolean NOT NULL DEFAULT true,
  CONSTRAINT booster_role_config_pkey PRIMARY KEY (guild_id)
);
CREATE TABLE public.booster_role_shares (
  id bigint NOT NULL DEFAULT nextval('booster_role_shares_id_seq'::regclass),
  guild_id bigint NOT NULL,
  owner_id bigint NOT NULL,
  role_id bigint NOT NULL,
  member_id bigint NOT NULL,
  added_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT booster_role_shares_pkey PRIMARY KEY (id)
);
CREATE TABLE public.booster_roles (
  id bigint NOT NULL DEFAULT nextval('booster_roles_id_seq'::regclass),
  guild_id bigint NOT NULL,
  user_id bigint NOT NULL,
  role_id bigint NOT NULL,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT booster_roles_pkey PRIMARY KEY (id)
);
CREATE TABLE public.bump_reminder_config (
  guild_id bigint NOT NULL,
  enabled boolean DEFAULT false,
  channel_id bigint,
  reminder_msg text,
  thankyou_msg text,
  autolock boolean DEFAULT false,
  autoclean boolean DEFAULT false,
  last_bump timestamp with time zone,
  next_bump timestamp with time zone,
  CONSTRAINT bump_reminder_config_pkey PRIMARY KEY (guild_id)
);
CREATE TABLE public.button_roles (
  id bigint NOT NULL DEFAULT nextval('button_roles_id_seq'::regclass),
  guild_id bigint NOT NULL,
  channel_id bigint NOT NULL,
  message_id bigint NOT NULL,
  role_id bigint NOT NULL,
  style text DEFAULT 'secondary'::text,
  emoji text,
  label text,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT button_roles_pkey PRIMARY KEY (id)
);
CREATE TABLE public.clownboard_config (
  guild_id bigint NOT NULL,
  channel_id bigint,
  emoji text DEFAULT '🤡'::text,
  threshold integer DEFAULT 3,
  color text,
  CONSTRAINT clownboard_config_pkey PRIMARY KEY (guild_id)
);
CREATE TABLE public.clownboard_ignores (
  id bigint NOT NULL DEFAULT nextval('clownboard_ignores_id_seq'::regclass),
  guild_id bigint NOT NULL,
  target_id bigint NOT NULL,
  target_type text NOT NULL CHECK (target_type = ANY (ARRAY['member'::text, 'channel'::text, 'role'::text])),
  CONSTRAINT clownboard_ignores_pkey PRIMARY KEY (id)
);
CREATE TABLE public.command_aliases (
  id bigint NOT NULL DEFAULT nextval('command_aliases_id_seq'::regclass),
  guild_id bigint NOT NULL,
  shortcut text NOT NULL,
  command text NOT NULL,
  owner_id bigint NOT NULL,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT command_aliases_pkey PRIMARY KEY (id)
);
CREATE TABLE public.counters (
  id bigint NOT NULL DEFAULT nextval('counters_id_seq'::regclass),
  guild_id bigint NOT NULL,
  channel_id bigint NOT NULL,
  type text NOT NULL,
  CONSTRAINT counters_pkey PRIMARY KEY (id)
);
CREATE TABLE public.disabled_commands (
  id bigint NOT NULL DEFAULT nextval('disabled_commands_id_seq'::regclass),
  guild_id bigint NOT NULL,
  command text NOT NULL,
  target_id bigint NOT NULL,
  target_type text NOT NULL CHECK (target_type = ANY (ARRAY['channel'::text, 'member'::text])),
  CONSTRAINT disabled_commands_pkey PRIMARY KEY (id)
);
CREATE TABLE public.disabled_events (
  id bigint NOT NULL DEFAULT nextval('disabled_events_id_seq'::regclass),
  guild_id bigint NOT NULL,
  event text NOT NULL,
  channel_id bigint NOT NULL,
  CONSTRAINT disabled_events_pkey PRIMARY KEY (id)
);
CREATE TABLE public.disabled_modules (
  id bigint NOT NULL DEFAULT nextval('disabled_modules_id_seq'::regclass),
  guild_id bigint NOT NULL,
  module text NOT NULL,
  channel_id bigint NOT NULL,
  CONSTRAINT disabled_modules_pkey PRIMARY KEY (id)
);
CREATE TABLE public.embed_templates (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  guild_id bigint NOT NULL,
  name text NOT NULL,
  title text,
  description text,
  color integer,
  footer text,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT embed_templates_pkey PRIMARY KEY (id)
);
CREATE TABLE public.fake_permissions (
  id bigint NOT NULL DEFAULT nextval('fake_permissions_id_seq'::regclass),
  guild_id bigint NOT NULL,
  role_id bigint NOT NULL,
  permission text NOT NULL,
  CONSTRAINT fake_permissions_pkey PRIMARY KEY (id)
);
CREATE TABLE public.filter_config (
  guild_id bigint NOT NULL,
  filter_snipe boolean NOT NULL DEFAULT false,
  CONSTRAINT filter_config_pkey PRIMARY KEY (guild_id)
);
CREATE TABLE public.filter_exemptions (
  id bigint NOT NULL DEFAULT nextval('filter_exemptions_id_seq'::regclass),
  guild_id bigint NOT NULL,
  filter_type text NOT NULL,
  role_id bigint,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  user_id bigint,
  CONSTRAINT filter_exemptions_pkey PRIMARY KEY (id)
);
CREATE TABLE public.filters (
  id bigint NOT NULL DEFAULT nextval('filters_id_seq'::regclass),
  guild_id bigint NOT NULL,
  type text NOT NULL,
  value text,
  channel_id bigint,
  setting text,
  parameters jsonb DEFAULT '{}'::jsonb,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT filters_pkey PRIMARY KEY (id)
);
CREATE TABLE public.forced_nicks (
  guild_id bigint NOT NULL,
  user_id bigint NOT NULL,
  nickname text NOT NULL,
  set_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT forced_nicks_pkey PRIMARY KEY (guild_id, user_id)
);
CREATE TABLE public.friend_group_bans (
  guild_id bigint NOT NULL,
  group_name text NOT NULL,
  user_id bigint NOT NULL,
  CONSTRAINT friend_group_bans_pkey PRIMARY KEY (guild_id, group_name, user_id)
);
CREATE TABLE public.friend_group_config (
  guild_id bigint NOT NULL,
  enabled boolean NOT NULL DEFAULT false,
  base_role_id bigint,
  base_position text NOT NULL DEFAULT 'below'::text CHECK (base_position = ANY (ARRAY['above'::text, 'below'::text])),
  group_limit integer NOT NULL DEFAULT 5,
  manager_role_id bigint,
  CONSTRAINT friend_group_config_pkey PRIMARY KEY (guild_id)
);
CREATE TABLE public.friend_group_filters (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  guild_id bigint NOT NULL,
  name text NOT NULL,
  CONSTRAINT friend_group_filters_pkey PRIMARY KEY (id)
);
CREATE TABLE public.friend_group_members (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  guild_id bigint NOT NULL,
  group_name text NOT NULL,
  user_id bigint NOT NULL,
  role text NOT NULL DEFAULT 'member'::text CHECK (role = ANY (ARRAY['member'::text, 'manager'::text, 'owner'::text])),
  CONSTRAINT friend_group_members_pkey PRIMARY KEY (id)
);
CREATE TABLE public.friend_groups (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  guild_id bigint NOT NULL,
  name text NOT NULL,
  member_limit integer NOT NULL DEFAULT 10,
  owner_id bigint,
  role_id bigint,
  vc_id bigint,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT friend_groups_pkey PRIMARY KEY (id)
);
CREATE TABLE public.giveaways (
  id bigint NOT NULL DEFAULT nextval('giveaways_id_seq'::regclass),
  guild_id bigint NOT NULL,
  channel_id bigint NOT NULL,
  message_id bigint,
  host_ids ARRAY NOT NULL,
  prize text NOT NULL,
  description text,
  winner_count integer NOT NULL DEFAULT 1,
  ends_at timestamp with time zone NOT NULL,
  ended boolean DEFAULT false,
  winners ARRAY DEFAULT '{}'::bigint[],
  required_roles ARRAY DEFAULT '{}'::bigint[],
  winner_roles ARRAY DEFAULT '{}'::bigint[],
  min_level integer,
  max_level integer,
  min_account_age integer,
  min_server_stay integer,
  embed_color text,
  image_url text,
  thumbnail_url text,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT giveaways_pkey PRIMARY KEY (id)
);
CREATE TABLE public.goodbye_messages (
  id bigint NOT NULL DEFAULT nextval('goodbye_messages_id_seq'::regclass),
  guild_id bigint NOT NULL,
  channel_id bigint NOT NULL,
  message text NOT NULL,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT goodbye_messages_pkey PRIMARY KEY (id)
);
CREATE TABLE public.guild_blacklist (
  id bigint NOT NULL DEFAULT nextval('guild_blacklist_id_seq'::regclass),
  target_id bigint NOT NULL,
  scope text NOT NULL CHECK (scope = ANY (ARRAY['user'::text, 'guild'::text])),
  reason text,
  banned_by bigint NOT NULL,
  banned_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT guild_blacklist_pkey PRIMARY KEY (id)
);
CREATE TABLE public.guild_config (
  guild_id bigint NOT NULL,
  prefix text NOT NULL DEFAULT ','::text,
  staff_roles ARRAY DEFAULT '{}'::bigint[],
  modlog_channel bigint,
  jail_channel bigint,
  muted_role bigint,
  imuted_role bigint,
  rmuted_role bigint,
  base_role bigint,
  autonick text,
  join_log_channel bigint,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  updated_at timestamp with time zone NOT NULL DEFAULT now(),
  greet_enabled boolean NOT NULL DEFAULT false,
  greet_channel bigint,
  greet_msg text,
  leave_enabled boolean NOT NULL DEFAULT false,
  leave_channel bigint,
  leave_msg text,
  ping_enabled boolean NOT NULL DEFAULT false,
  bot_lock boolean NOT NULL DEFAULT false,
  lockdown_staff_role bigint,
  log_color integer NOT NULL DEFAULT 16432620,
  member_log_channel bigint,
  mod_log_channel bigint,
  role_log_channel bigint,
  channel_log_channel bigint,
  voice_log_channel bigint,
  general_log_channel bigint,
  CONSTRAINT guild_config_pkey PRIMARY KEY (guild_id)
);
CREATE TABLE public.guild_whitelist (
  guild_id bigint NOT NULL,
  added_by bigint NOT NULL,
  added_at timestamp with time zone NOT NULL DEFAULT now(),
  note text,
  CONSTRAINT guild_whitelist_pkey PRIMARY KEY (guild_id)
);
CREATE TABLE public.highlight_ignores (
  id bigint NOT NULL DEFAULT nextval('highlight_ignores_id_seq'::regclass),
  user_id bigint NOT NULL,
  guild_id bigint NOT NULL,
  target_id bigint NOT NULL,
  target_type text NOT NULL CHECK (target_type = ANY (ARRAY['member'::text, 'channel'::text, 'role'::text])),
  CONSTRAINT highlight_ignores_pkey PRIMARY KEY (id)
);
CREATE TABLE public.highlights (
  id bigint NOT NULL DEFAULT nextval('highlights_id_seq'::regclass),
  user_id bigint NOT NULL,
  guild_id bigint NOT NULL,
  keyword text NOT NULL,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT highlights_pkey PRIMARY KEY (id)
);
CREATE TABLE public.ignored_targets (
  id bigint NOT NULL DEFAULT nextval('ignored_targets_id_seq'::regclass),
  guild_id bigint NOT NULL,
  target_id bigint NOT NULL,
  target_type text NOT NULL CHECK (target_type = ANY (ARRAY['member'::text, 'channel'::text])),
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT ignored_targets_pkey PRIMARY KEY (id)
);
CREATE TABLE public.imgonly_channels (
  id bigint NOT NULL DEFAULT nextval('imgonly_channels_id_seq'::regclass),
  guild_id bigint NOT NULL,
  channel_id bigint NOT NULL,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT imgonly_channels_pkey PRIMARY KEY (id)
);
CREATE TABLE public.insights_config (
  guild_id bigint NOT NULL,
  enabled boolean DEFAULT false,
  enabled_at timestamp with time zone,
  CONSTRAINT insights_config_pkey PRIMARY KEY (guild_id)
);
CREATE TABLE public.invoke_messages (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  guild_id bigint NOT NULL,
  action text NOT NULL,
  delivery text NOT NULL,
  message text NOT NULL,
  CONSTRAINT invoke_messages_pkey PRIMARY KEY (id)
);
CREATE TABLE public.jailed_members (
  guild_id bigint NOT NULL,
  user_id bigint NOT NULL,
  jailed_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT jailed_members_pkey PRIMARY KEY (guild_id, user_id)
);
CREATE TABLE public.level_config (
  guild_id bigint NOT NULL,
  enabled boolean DEFAULT true,
  xp_multiplier numeric DEFAULT 1.0,
  message text,
  message_mode text DEFAULT 'channel'::text CHECK (message_mode = ANY (ARRAY['channel'::text, 'dm'::text, 'off'::text])),
  leaderboard_title text DEFAULT 'Leaderboard'::text,
  stack_roles boolean DEFAULT false,
  ignored_channels ARRAY DEFAULT '{}'::bigint[],
  ignored_roles ARRAY DEFAULT '{}'::bigint[],
  channel_id bigint,
  levelup_msg text,
  CONSTRAINT level_config_pkey PRIMARY KEY (guild_id)
);
CREATE TABLE public.level_roles (
  id bigint NOT NULL DEFAULT nextval('level_roles_id_seq'::regclass),
  guild_id bigint NOT NULL,
  role_id bigint NOT NULL,
  level integer NOT NULL,
  CONSTRAINT level_roles_pkey PRIMARY KEY (id)
);
CREATE TABLE public.levels (
  user_id bigint NOT NULL,
  guild_id bigint NOT NULL,
  xp integer NOT NULL DEFAULT 0,
  level integer NOT NULL DEFAULT 0,
  total_xp integer NOT NULL DEFAULT 0,
  updated_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT levels_pkey PRIMARY KEY (user_id, guild_id)
);
CREATE TABLE public.log_config (
  id bigint NOT NULL DEFAULT nextval('log_config_id_seq'::regclass),
  guild_id bigint NOT NULL,
  event text NOT NULL,
  channel_id bigint NOT NULL,
  color text,
  tier2_event boolean DEFAULT false,
  CONSTRAINT log_config_pkey PRIMARY KEY (id)
);
CREATE TABLE public.log_ignores (
  id bigint NOT NULL DEFAULT nextval('log_ignores_id_seq'::regclass),
  guild_id bigint NOT NULL,
  target_id bigint NOT NULL,
  target_type text NOT NULL CHECK (target_type = ANY (ARRAY['member'::text, 'channel'::text])),
  CONSTRAINT log_ignores_pkey PRIMARY KEY (id)
);
CREATE TABLE public.mod_cases (
  id bigint NOT NULL DEFAULT nextval('mod_cases_id_seq'::regclass),
  case_id integer NOT NULL,
  guild_id bigint NOT NULL,
  target_id bigint NOT NULL,
  moderator_id bigint NOT NULL,
  action text NOT NULL,
  reason text,
  duration interval,
  expires_at timestamp with time zone,
  active boolean DEFAULT true,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT mod_cases_pkey PRIMARY KEY (id)
);
CREATE TABLE public.msg_stats (
  id bigint NOT NULL DEFAULT nextval('msg_stats_id_seq'::regclass),
  guild_id bigint NOT NULL,
  channel_id bigint NOT NULL,
  user_id bigint NOT NULL,
  msg_date date NOT NULL DEFAULT CURRENT_DATE,
  count integer NOT NULL DEFAULT 1,
  CONSTRAINT msg_stats_pkey PRIMARY KEY (id)
);
CREATE TABLE public.name_history (
  id bigint NOT NULL DEFAULT nextval('name_history_id_seq'::regclass),
  user_id bigint NOT NULL,
  guild_id bigint,
  name text NOT NULL,
  type text NOT NULL CHECK (type = ANY (ARRAY['username'::text, 'nickname'::text, 'guild_name'::text])),
  changed_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT name_history_pkey PRIMARY KEY (id)
);
CREATE TABLE public.noselfreact_config (
  guild_id bigint NOT NULL,
  enabled boolean DEFAULT false,
  staff_bypass boolean DEFAULT false,
  punishment text DEFAULT 'warn'::text,
  monitored_emojis ARRAY DEFAULT '{}'::text[],
  CONSTRAINT noselfreact_config_pkey PRIMARY KEY (guild_id)
);
CREATE TABLE public.noselfreact_exemptions (
  id bigint NOT NULL DEFAULT nextval('noselfreact_exemptions_id_seq'::regclass),
  guild_id bigint NOT NULL,
  target_id bigint NOT NULL,
  target_type text NOT NULL CHECK (target_type = ANY (ARRAY['member'::text, 'channel'::text, 'role'::text])),
  CONSTRAINT noselfreact_exemptions_pkey PRIMARY KEY (id)
);
CREATE TABLE public.notes (
  id bigint NOT NULL DEFAULT nextval('notes_id_seq'::regclass),
  guild_id bigint NOT NULL,
  target_id bigint NOT NULL,
  moderator_id bigint NOT NULL,
  content text NOT NULL,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT notes_pkey PRIMARY KEY (id)
);
CREATE TABLE public.ping_assignments (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  guild_id bigint NOT NULL,
  channel_id bigint NOT NULL,
  autodelete integer NOT NULL DEFAULT 3,
  CONSTRAINT ping_assignments_pkey PRIMARY KEY (id)
);
CREATE TABLE public.reaction_messages (
  id bigint NOT NULL DEFAULT nextval('reaction_messages_id_seq'::regclass),
  guild_id bigint NOT NULL,
  channel_id bigint NOT NULL,
  emojis ARRAY NOT NULL,
  CONSTRAINT reaction_messages_pkey PRIMARY KEY (id)
);
CREATE TABLE public.reaction_roles (
  id bigint NOT NULL DEFAULT nextval('reaction_roles_id_seq'::regclass),
  guild_id bigint NOT NULL,
  channel_id bigint NOT NULL,
  message_id bigint NOT NULL,
  reaction text NOT NULL,
  role_id bigint NOT NULL,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT reaction_roles_pkey PRIMARY KEY (id)
);
CREATE TABLE public.reaction_triggers (
  id bigint NOT NULL DEFAULT nextval('reaction_triggers_id_seq'::regclass),
  guild_id bigint NOT NULL,
  trigger text NOT NULL,
  emoji text NOT NULL,
  type text NOT NULL DEFAULT 'current'::text CHECK (type = ANY (ARRAY['current'::text, 'previous'::text])),
  owner_id bigint NOT NULL,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT reaction_triggers_pkey PRIMARY KEY (id)
);
CREATE TABLE public.reminders (
  id bigint NOT NULL DEFAULT nextval('reminders_id_seq'::regclass),
  user_id bigint NOT NULL,
  guild_id bigint,
  channel_id bigint,
  content text NOT NULL,
  remind_at timestamp with time zone NOT NULL,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  fired boolean DEFAULT false,
  CONSTRAINT reminders_pkey PRIMARY KEY (id)
);
CREATE TABLE public.restrict_commands (
  id bigint NOT NULL DEFAULT nextval('restrict_commands_id_seq'::regclass),
  guild_id bigint NOT NULL,
  command text NOT NULL,
  role_id bigint NOT NULL,
  CONSTRAINT restrict_commands_pkey PRIMARY KEY (id)
);
CREATE TABLE public.seen (
  user_id bigint NOT NULL,
  guild_id bigint NOT NULL,
  last_seen timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT seen_pkey PRIMARY KEY (user_id, guild_id)
);
CREATE TABLE public.snipe_cache (
  id bigint NOT NULL DEFAULT nextval('snipe_cache_id_seq'::regclass),
  guild_id bigint NOT NULL,
  channel_id bigint NOT NULL,
  author_id bigint NOT NULL,
  content text,
  attachments ARRAY DEFAULT '{}'::text[],
  type text NOT NULL CHECK (type = ANY (ARRAY['delete'::text, 'edit'::text, 'reaction'::text])),
  extra jsonb DEFAULT '{}'::jsonb,
  sniped_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT snipe_cache_pkey PRIMARY KEY (id)
);
CREATE TABLE public.spotify_tokens (
  user_id bigint NOT NULL,
  access_token text NOT NULL,
  refresh_token text NOT NULL,
  expires_at timestamp with time zone NOT NULL,
  scope text,
  connected_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT spotify_tokens_pkey PRIMARY KEY (user_id)
);
CREATE TABLE public.starboard_config (
  guild_id bigint NOT NULL,
  channel_id bigint,
  enabled boolean DEFAULT true,
  emoji text DEFAULT '⭐'::text,
  threshold integer DEFAULT 3,
  color text,
  selfstar boolean DEFAULT false,
  show_jumpurl boolean DEFAULT true,
  show_timestamp boolean DEFAULT true,
  show_attachments boolean DEFAULT true,
  CONSTRAINT starboard_config_pkey PRIMARY KEY (guild_id)
);
CREATE TABLE public.starboard_ignores (
  id bigint NOT NULL DEFAULT nextval('starboard_ignores_id_seq'::regclass),
  guild_id bigint NOT NULL,
  target_id bigint NOT NULL,
  target_type text NOT NULL CHECK (target_type = ANY (ARRAY['member'::text, 'channel'::text, 'role'::text])),
  CONSTRAINT starboard_ignores_pkey PRIMARY KEY (id)
);
CREATE TABLE public.sticky_messages (
  id bigint NOT NULL DEFAULT nextval('sticky_messages_id_seq'::regclass),
  guild_id bigint NOT NULL,
  channel_id bigint NOT NULL,
  message text NOT NULL,
  last_msg_id bigint,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT sticky_messages_pkey PRIMARY KEY (id)
);
CREATE TABLE public.sticky_roles (
  id bigint NOT NULL DEFAULT nextval('sticky_roles_id_seq'::regclass),
  guild_id bigint NOT NULL,
  user_id bigint NOT NULL,
  role_id bigint NOT NULL,
  CONSTRAINT sticky_roles_pkey PRIMARY KEY (id)
);
CREATE TABLE public.sudo_users (
  user_id bigint NOT NULL,
  granted_by bigint NOT NULL,
  granted_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT sudo_users_pkey PRIMARY KEY (user_id)
);
CREATE TABLE public.temp_roles (
  id bigint NOT NULL DEFAULT nextval('temp_roles_id_seq'::regclass),
  guild_id bigint NOT NULL,
  user_id bigint NOT NULL,
  role_id bigint NOT NULL,
  expires_at timestamp with time zone NOT NULL,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT temp_roles_pkey PRIMARY KEY (id)
);
CREATE TABLE public.ticket_config (
  guild_id bigint NOT NULL,
  category_id bigint,
  support_role_id bigint,
  log_channel_id bigint,
  welcome_message text,
  CONSTRAINT ticket_config_pkey PRIMARY KEY (guild_id)
);
CREATE TABLE public.ticket_managers (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  guild_id bigint NOT NULL,
  target_id bigint NOT NULL,
  target_type text NOT NULL CHECK (target_type = ANY (ARRAY['user'::text, 'role'::text])),
  CONSTRAINT ticket_managers_pkey PRIMARY KEY (id)
);
CREATE TABLE public.tickets (
  id bigint NOT NULL DEFAULT nextval('tickets_id_seq'::regclass),
  guild_id bigint NOT NULL,
  channel_id bigint NOT NULL,
  owner_id bigint NOT NULL,
  status text DEFAULT 'open'::text CHECK (status = ANY (ARRAY['open'::text, 'closed'::text, 'archived'::text])),
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  closed_at timestamp with time zone,
  CONSTRAINT tickets_pkey PRIMARY KEY (id)
);
CREATE TABLE public.tiers (
  id bigint NOT NULL DEFAULT nextval('tiers_id_seq'::regclass),
  target_id bigint NOT NULL,
  scope text NOT NULL CHECK (scope = ANY (ARRAY['user'::text, 'guild'::text])),
  tier integer NOT NULL CHECK (tier = ANY (ARRAY[1, 2])),
  granted_by bigint NOT NULL,
  granted_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT tiers_pkey PRIMARY KEY (id)
);
CREATE TABLE public.timers (
  id bigint NOT NULL DEFAULT nextval('timers_id_seq'::regclass),
  guild_id bigint NOT NULL,
  channel_id bigint NOT NULL,
  message text NOT NULL,
  interval_secs integer NOT NULL,
  require_activity boolean DEFAULT false,
  last_sent timestamp with time zone,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT timers_pkey PRIMARY KEY (id)
);
CREATE TABLE public.timezones (
  user_id bigint NOT NULL,
  timezone text NOT NULL,
  set_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT timezones_pkey PRIMARY KEY (user_id)
);
CREATE TABLE public.voicecentre_channels (
  channel_id bigint NOT NULL,
  guild_id bigint NOT NULL,
  owner_id bigint NOT NULL,
  locked boolean DEFAULT false,
  hidden boolean DEFAULT false,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT voicecentre_channels_pkey PRIMARY KEY (channel_id)
);
CREATE TABLE public.voicecentre_config (
  guild_id bigint NOT NULL,
  enabled boolean DEFAULT false,
  create_channel_id bigint,
  category_id bigint,
  private_category_id bigint,
  default_name text DEFAULT '{username} channel'::text,
  default_bitrate integer DEFAULT 64000,
  default_region text,
  default_role_id bigint,
  send_interface boolean DEFAULT true,
  join_role_id bigint,
  CONSTRAINT voicecentre_config_pkey PRIMARY KEY (guild_id)
);
CREATE TABLE public.warn_strikes (
  guild_id bigint NOT NULL,
  strike integer NOT NULL,
  action text NOT NULL,
  CONSTRAINT warn_strikes_pkey PRIMARY KEY (guild_id, strike)
);
CREATE TABLE public.warnings (
  id bigint NOT NULL DEFAULT nextval('warnings_id_seq'::regclass),
  guild_id bigint NOT NULL,
  target_id bigint NOT NULL,
  moderator_id bigint NOT NULL,
  reason text,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT warnings_pkey PRIMARY KEY (id)
);
CREATE TABLE public.webhooks (
  id bigint NOT NULL DEFAULT nextval('webhooks_id_seq'::regclass),
  guild_id bigint NOT NULL,
  channel_id bigint NOT NULL,
  webhook_id bigint NOT NULL,
  webhook_url text NOT NULL,
  name text NOT NULL,
  owner_id bigint NOT NULL,
  locked boolean DEFAULT false,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT webhooks_pkey PRIMARY KEY (id)
);
CREATE TABLE public.welcome_messages (
  id bigint NOT NULL DEFAULT nextval('welcome_messages_id_seq'::regclass),
  guild_id bigint NOT NULL,
  channel_id bigint NOT NULL,
  message text NOT NULL,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT welcome_messages_pkey PRIMARY KEY (id)
);
```


## Troubleshooting

- **Connection Error**: Verify SUPABASE_URL and SUPABASE_KEY in .env
- **Table Not Found**: Make sure you've created the tables with the SQL above
- **Permission Denied**: Check Row Level Security (RLS) policies if enabled
