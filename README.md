# 🤖 File Store Bot — Pyrogram

Permanent file storage Telegram bot with shareable links.

## ✨ Features
- 📁 **File Store** — Store any file and get a permanent shareable link
- 📦 **Batch Store** — Store multiple sequential files under one link
- 📦 **Custom Batch** — Store non-sequential / forwarded messages under one link
- 🔗 **Special Link** — Editable links (change target file anytime!)
- 🌐 **Universal Link** — Links that work across all clone bots sharing same DB
- ✂️ **Link Shortener** — Shorten any URL via TinyURL
- 📢 **Force Subscribe** — Users must join a channel before using the bot
- 📡 **Broadcast** — Send a message to all users
- 🚫 **Ban / Unban** — Block or restore users
- 📊 **Stats** — See total user count
- ⚙️ **User Settings** — Auto-delete, notifications, language toggles
- ⚡ **Clone Info** — Instructions to deploy your own clone

---

## 🚀 Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Create a `.env` file
Copy `.env.example` to `.env` and fill in your values:
```bash
cp .env.example .env
```

**Variables explained:**

| Variable | Description |
|---|---|
| `API_ID` | From https://my.telegram.org |
| `API_HASH` | From https://my.telegram.org |
| `BOT_TOKEN` | From @BotFather |
| `OWNER_ID` | Your Telegram user ID |
| `DATABASE_URL` | MongoDB connection string |
| `FORCE_SUB_CHANNEL` | Channel ID (e.g. `-1001234567890`). Set `0` to disable. |
| `FILE_DB_CHANNEL` | Private channel where files are stored (bot must be admin) |

### 3. Prepare Channels

**Force Sub Channel:**
- Create a public or private channel
- Add the bot as **admin**
- Copy its ID (use @userinfobot) → set as `FORCE_SUB_CHANNEL`

**File DB Channel:**
- Create a **private** channel
- Add the bot as **admin** with "Post Messages" permission
- Copy its ID → set as `FILE_DB_CHANNEL`

### 4. Run the bot
```bash
# Load .env and run
export $(cat .env | xargs) && python main.py
```

Or using python-dotenv:
```bash
pip install python-dotenv
```
Then add at top of `main.py`:
```python
from dotenv import load_dotenv
load_dotenv()
```

---

## 📂 Project Structure
```
filestore-bot/
├── main.py              # Bot entry point
├── config.py            # Configuration
├── database.py          # MongoDB helpers
├── state.py             # Shared in-memory state
├── requirements.txt
├── .env.example
└── plugins/
    ├── start.py         # /start, /help, /about + force-sub + settings callbacks
    ├── files.py         # File store handler
    ├── batch.py         # /batch, /done, /cancel
    ├── settings.py      # /settings command
    ├── mod_features.py  # /special_link, /universal_link, /custom_batch, /shortener
    └── admin.py         # /ban, /unban, /stats, /broadcast
```

---

## 💬 Bot Commands

### User Commands
| Command | Description |
|---|---|
| `/start` | Start the bot |
| `/help` | Show help menu |
| `/about` | About the bot |
| `/settings` | Toggle auto-delete, notifications, language |
| `/batch` | Start storing multiple sequential files |
| `/custom_batch` | Store non-sequential forwarded messages |
| `/shortener <url>` | Shorten any link |
| `/done` | Finish batch & get link |
| `/cancel` | Cancel active session |

### Mod / Admin Commands (Owner Only)
| Command | Description |
|---|---|
| `/special_link` | Reply to file → get editable link |
| `/update_link <id>` | Reply to new file → update link target |
| `/mylinks` | List all your special links |
| `/universal_link` | Reply to file → multi-clone accessible link |
| `/ban <user_id>` | Ban a user |
| `/unban <user_id>` | Unban a user |
| `/stats` | Show total users |
| `/broadcast` | Broadcast (reply to a message) |

---

## 🔗 How File Links Work
1. User sends a file → bot forwards it to `FILE_DB_CHANNEL`
2. Bot generates: `https://t.me/YOUR_BOT?start=<message_id>`
3. Anyone who clicks the link → bot sends them the file
