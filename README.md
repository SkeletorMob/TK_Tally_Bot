# TK Tally Bot ☠️

A Discord bot that keeps a running tally of treasonous team kills, roasts the traitor on the spot, and hands out escalating roles of dishonor.

## Commands

| Command | What it does |
|---|---|
| `/tk killer [victim] [weapon] [game] [style]` | Report a TK. Victim defaults to you. Style: Random, Kyle, Obituary, Breaking news, Pun |
| Right-click a user → **Apps → They TK'd me!** | One-click report with you as the victim |
| `/tally [member]` | Rap sheet: TKs, times betrayed, self-kills, rank, favorite victim, nemesis, achievements |
| `/leaderboard` | Hall of Shame (top team killers) |
| `/victims` | Most betrayed players |
| `/roast member` | Roast someone based on their record |
| `/forgive killer` | Victim wipes the last TK that person did on them |
| `/undo` | Take back your own last report (within 15 min) |
| `/ranks` | Show the rank ladder and achievements |
| `/tkadmin reset / roles / syncroles / add` | Admin tools (needs Manage Server) |

Killing yourself counts as a **self-inflicted** TK. It gets its own roast but doesn't count toward rank.

## Ranks (auto-assigned roles)

1 Friendly Fire Enthusiast · 3 Blue on Blue · 5 Spawn Camper (Own Spawn) · 10 Benedict Arnold · 15 Et Tu, Brute? · 25 Certified War Criminal · 50 Double Agent · 100 The Traitor King

The bot creates these roles the first time someone earns one, and a member only holds their current rank. Edit the names, thresholds and colors in `tktally/ranks.py`. Add roast lines in `tktally/roasts.py`.

## Setup

1. **Create the bot.** Go to https://discord.com/developers/applications → New Application → **Bot** → Reset Token and copy the token. No privileged intents are needed.
2. **Invite it.** Go to OAuth2 → URL Generator. Scopes: `bot`, `applications.commands`. Bot permissions: **Manage Roles**, Send Messages, Embed Links. Open the generated URL and pick your server.
3. **Role order.** In Server Settings → Roles, drag the bot's role **above** the TK rank roles. If you skip this, it can't assign them.
4. **Run it:**
   ```bash
   python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   cp .env.example .env        # paste your token into DISCORD_TOKEN
   python -m tktally
   ```
   While testing, set `DEV_GUILD_ID` to your server's ID so slash commands update instantly. Without it, they sync globally, which can take a while.

Data is stored in `tktally.db` (SQLite), separately for each server. Run the tests with `pip install pytest && pytest`.

## Hosting

To keep the bot online, it has to run continuously somewhere, for example a Raspberry Pi, a small VPS, or Railway/Fly.io. Make sure the database file sits on persistent storage.
