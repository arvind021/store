from pyrogram import Client
from config import Config

app = Client(
    "FileStoreBot",
    api_id    = Config.API_ID,
    api_hash  = Config.API_HASH,
    bot_token = Config.BOT_TOKEN,
    plugins   = dict(root="plugins")
)

if __name__ == "__main__":
    print("🤖 File Store Bot starting...")
    app.run()
    print("✅ Bot stopped.")
