# TK Tally Bot ☠️

A Discord bot that keeps a running tally of treasonous team kills, roasts the traitor on the spot, and hands out escalating roles of dishonor. Built for shooter-game servers where friendly fire is a way of life.

## License

TK Tally Bot is licensed under [PolyForm Noncommercial 1.0.0](LICENSE). You're free to use, modify and self-host it for personal or noncommercial purposes. Commercial use requires permission; [open an issue](https://github.com/SkeletorMob/TK_Tally_Bot/issues) to ask.

## Add it to your server

**[➕ Invite TK Tally Bot](INVITE_LINK_HERE)**

After it joins, go to **Server Settings → Roles** and drag the **TK Tally Bot** role near the top. It needs to sit above the rank roles it hands out, or promotions won't work.

That's all the setup. Type `/tk` to report your first traitor.

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

## Ranks

| TKs | Role |
|---|---|
| 1 | Friendly Fire Enthusiast |
| 3 | Blue on Blue |
| 5 | Spawn Camper (Own Spawn) |
| 10 | Benedict Arnold |
| 15 | Et Tu, Brute? |
| 25 | Certified War Criminal |
| 50 | Double Agent |
| 100 | The Traitor King |

The bot creates each role the first time someone earns it, and a member only holds their current rank. If you'd rather it didn't manage roles, turn it off with `/tkadmin roles enabled:False`.

## Achievements

🩸 First Blood (Wrong Kind) · 🔁 Repeat Customer · 🔥 Killing Spree (Of Friends) · ⚖️ Equal Opportunity Traitor · 🗡️ Vendetta · 🪞 The Call Is Coming From Inside the House · 🛡️ Human Shield · 🎯 Professional Pincushion

Use `/ranks` in Discord to see what each one takes.

## Privacy & terms

TK Tally only stores Discord IDs and the TK records themselves. It never reads your messages. See the [Privacy Policy](PRIVACY.md) and [Terms of Service](TERMS.md).

Found a bug or want your data removed? [Open an issue](https://github.com/SkeletorMob/TK_Tally_Bot/issues).

---

## Self-hosting

If you'd rather run your own copy of the bot:

1. **Create an application** at https://discord.com/developers/applications → New Application → **Bot** → Reset Token, and copy the token. No privileged intents are needed.
2. **Invite it** via OAuth2 → URL Generator with scopes `bot` and `applications.commands`, and permissions **Manage Roles**, **Send Messages** and **Embed Links**.
3. **Install and run** (Python 3.10+):
   ```bash
   python -m venv .venv
   source .venv/bin/activate        # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   cp .env.example .env             # then paste your token into DISCORD_TOKEN
   python -m tktally
   ```

| `.env` setting | Purpose |
|---|---|
| `DISCORD_TOKEN` | Your bot token (required) |
| `DEV_GUILD_ID` | A test server ID. Commands sync there instantly instead of globally. Leave it blank in production. |
| `TK_DB_PATH` | Where the SQLite database is stored (default `tktally.db`). Use a full path, and keep it out of synced folders like OneDrive. |

Customize the rank names and thresholds in `tktally/ranks.py`, and add roast lines in `tktally/roasts.py`. Run the tests with `pip install pytest && pytest`.
