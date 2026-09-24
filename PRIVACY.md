# TK Tally Bot: Privacy Policy

*Last updated: September 24, 2026*

TK Tally Bot ("the bot") is a hobby Discord bot that keeps a humorous tally of team kills. This policy explains what it stores and what you can do about it.

## What the bot stores

Only what's needed to keep the tally:

- **Discord user IDs**: of the person who did the team kill, the victim, and whoever reported it
- **Discord server IDs**: so each server's tally stays separate
- **Team kill records**: the optional weapon and game text someone typed in, plus the time of the report
- **Achievements** each user has earned in each server
- **Server settings**, such as whether automatic rank roles are turned on

## What the bot does *not* store

- Message content. The bot only responds to its own slash commands and doesn't read chat.
- Usernames, avatars, email addresses, IP addresses, voice data or direct messages.

Usernames and avatars that appear in bot replies are fetched from Discord when the reply is shown and aren't saved.

## How the data is used

The data is used only to run the bot's features: tallies, leaderboards, ranks, roles, achievements and roasts. It is not sold or shared with anyone, and it is not used for advertising, analytics or AI training.

## Where it's kept

Records are stored in a database on the machine that runs the bot. That machine is controlled by the bot's operator. Discord also processes interactions under [Discord's own Privacy Policy](https://discord.com/privacy).

## How long it's kept

Records are kept until they're deleted in one of these ways:

- `/undo`: the reporter removes their own report (within 15 minutes)
- `/forgive`: a victim removes a team kill made against them
- `/tkadmin reset`: a server admin wipes a member's records and achievements
- Asking the developer to delete it (see below)

Removing the bot from a server does not automatically erase that server's records. Ask if you want them gone.

## Your choices

To have your data deleted, open an issue at https://github.com/SkeletorMob/TK_Tally_Bot/issues, or contact the developer on Discord. Include your Discord user ID or server ID. Requests are handled as soon as reasonably possible.

## Children

The bot is meant for users who meet Discord's minimum age requirement. It does not knowingly collect any extra information about anyone.

## Changes

If this policy changes, the updated version will be posted here with a new date.
