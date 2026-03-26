# How to Get Your Supabase API Key

## Step 1: Go to Supabase Dashboard
Visit: https://supabase.com/dashboard/projects

## Step 2: Select Your Project
- If you already have a project, click on it
- If not, click "New Project" to create one

## Step 3: Navigate to API Settings
1. In your project dashboard, look for the ⚙️ **Settings** icon in the left sidebar
2. Click on **API** in the settings menu

## Step 4: Copy Your Credentials
You'll see two important values:

### Project URL
```
https://xxxxxxxxxxxxx.supabase.co
```
Copy this entire URL

### API Keys Section
Find the "anon public" key (NOT the service_role key)
- It starts with `eyJ...`
- It's very long (200+ characters)
- Example format: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZ...`

## Step 5: Update Your .env File

Open `.env` and replace with:

```env
# Supabase Configuration
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.your-actual-key-here...

# Flask Configuration
FLASK_SECRET_KEY=0747f30ea78fb67a5b58976f9f683f70bae6952d9b9774fa
FLASK_ENV=development
```

## Visual Guide

When you're on the API settings page, it looks like this:

```
┌─────────────────────────────────────────┐
│ Project API                             │
├─────────────────────────────────────────┤
│                                         │
│ URL                                     │
│ https://xxxxx.supabase.co              │
│ [Copy]                                  │
│                                         │
│ API Keys                                │
│                                         │
│ anon public ⚠️ Safe to use in browser  │
│ eyJhbGciOiJIUzI1NiIsInR5cCI6...       │
│ [Copy]                                  │
│                                         │
│ service_role ⛔ Keep this secret       │
│ eyJhbGciOiJIUzI1NiIsInR5cCI6...       │
│ [Copy]                                  │
│                                         │
└─────────────────────────────────────────┘
```

## Important Notes

- ✅ Use the **anon public** key (starts with eyJ...)
- ❌ Do NOT use the service_role key
- ❌ Do NOT use keys starting with `sb_publishable_`
- The key should be at least 200 characters long

## If You Don't Have a Supabase Account

1. Go to https://supabase.com
2. Click "Start your project"
3. Sign up (free tier available)
4. Create a new project
5. Wait 2-3 minutes for it to initialize
6. Follow steps above to get your keys

## Need Help Setting Up Database?

After getting your API keys, you'll need to create database tables.
See `SETUP.md` for the SQL commands to create the required tables.
