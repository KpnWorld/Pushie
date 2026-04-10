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

## Troubleshooting

- **Connection Error**: Verify SUPABASE_URL and SUPABASE_KEY in .env
- **Table Not Found**: Make sure you've created the tables with the SQL above
- **Permission Denied**: Check Row Level Security (RLS) policies if enabled
