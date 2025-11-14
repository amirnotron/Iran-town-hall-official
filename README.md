<!--
  Consolidated README.md
  Merged content from SETUP.md, QUICK_START.md, and RESTRUCTURE_SUMMARY.md.
-->

# Iran Town Hall — Discord Bot

![Project Banner](https://cdn.discordapp.com/attachments/1236751646147608618/1438998225909584097/b8be515a916cc50a27490ab518978677.webp?ex=6918eb08&is=69179988&hm=fe4e226c452ba670c4b287789c2a7dc4615a3566661818aa4a0ce1eb2307a9f8&)

A modular Discord bot with moderation, leveling, giveaways, ticket modals, anti-spam, and anti-link protection.

---

## Quick Start

1. Install Python 3.8+ and the dependencies:

```powershell
pip install -r requirements.txt
```

2. Edit `config/settings.json` and set your `bot.token`, channel IDs, and role IDs.

3. Run the bot:

```powershell
python bot_main.py
```

Tip: wait ~30 seconds after the bot starts for slash commands to appear in Discord.

---

## Project Structure

```
iran-town-hall/
├── config/                    # Configuration files
│   └── settings.json          # Main configuration file (edit this)
├── commands/                  # Command cogs (moderation, ticket, leveling, etc.)
├── utils/                     # Helper utilities (config, db, helpers)
├── events/                    # Event handlers (on_member_join, etc.)
├── db/                        # SQLite databases (auto-created)
├── bot_main.py                # Main entrypoint — run this
└── README.md                  # This file (consolidated documentation)
```

---

## Features

- Moderation: `/ban`, `/kick`, `/timeout`, `/warn`
- Leveling: message + voice XP, `/level` command
- Tickets: modal-based ticket form with Product, Name, Date, and Description; transcript archiving
- Anti-Spam: global spam detection and configurable punishments
- Anti-Link: detects and removes Discord invites & blocked domains; deletes message and times out offender (configurable)
- Giveaways: `/gstart`, invite tracking, winner selection
- Utilities: `/ping`, `/userinfo`, `/serverinfo`, `/clear`

---

## Configuration

Edit `config/settings.json` to customize the bot. Example snippets:

```json
{
  "bot": { "token": "YOUR_BOT_TOKEN_HERE", "command_prefix": "!" },
  "channels": {
    "level_up_channel_id": 1234567890,
    "ticket_channel_id": 1234567890,
    "transcript_channel_id": 1234567890
  },
  "roles": {
    "member_role_id": 1234567890,
    "moderator_role_ids": [1234567890]
  },
  "features": {
    "leveling": { "enabled": true },
    "antispam": { "enabled": true },
    "antilink": { "enabled": true, "delete_message": true, "timeout_minutes": 5 }
  }
}
```

Make sure to replace placeholder IDs and the token before running the bot.

---

## Running & Common Commands

- Start the bot: `python bot_main.py`
- Setup ticket panel: `/setup_tickets` in the configured ticket channel
- Enable anti-spam: `/antispam enable`

Command highlights:

- Moderation: `/ban`, `/kick`, `/timeout`, `/warn`
- Leveling: `/level`
- Tickets: `/setup_tickets` → users fill a modal to open tickets
- Giveaways: `/gstart duration:<1d|7d> winners:1 required_invites:0 prize:"text"`

---

## Databases

The bot creates SQLite DB files in `db/` automatically:
- `levels.db` — user XP and levels
- `warnings.db` — moderation warnings
- `antispam.db` — anti-spam records
- `giveaway.db` — giveaway data
- `tickets.db` — ticket records

---

Made with ❤️ by not_notron for the Iran Town Hall community
