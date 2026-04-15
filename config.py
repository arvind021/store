import os

class Config:
    # ── Telegram Credentials ──────────────────────────────
    API_ID        = int(os.environ.get("API_ID", 0))
    API_HASH      = os.environ.get("API_HASH", "")
    BOT_TOKEN     = os.environ.get("BOT_TOKEN", "")

    # ── Owner & Admins ────────────────────────────────────
    OWNER_ID      = int(os.environ.get("OWNER_ID", 0))
    ADMINS        = [OWNER_ID]

    # ── MongoDB ───────────────────────────────────────────
    DATABASE_URL  = os.environ.get("DATABASE_URL", "mongodb://localhost:27017")
    DATABASE_NAME = "FilestoreBot"

    # ── Force Subscribe Channel ───────────────────────────
    # Set to channel ID (e.g. -1001234567890) or leave "0" to disable
    FORCE_SUB_CHANNEL = os.environ.get("FORCE_SUB_CHANNEL", "0")

    # ── File DB Channel ───────────────────────────────────
    # Private channel where files are stored (bot must be admin)
    FILE_DB_CHANNEL = int(os.environ.get("FILE_DB_CHANNEL", 0))

    # ── Log Channel (optional) ────────────────────────────
    LOG_CHANNEL   = int(os.environ.get("LOG_CHANNEL", 0))
