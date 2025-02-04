import os
import time
import requests
import dropbox
import asyncio
import threading
from urllib.parse import urlparse, unquote
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ✅ Flask app
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running successfully!"

# ✅ Telegram bot token
TELEGRAM_BOT_TOKEN = "5876860733:AAFAPmqGHd0NDI-tatG8FboMuMEwE9dOGYA"

# ✅ Dropbox Credentials
DROPBOX_APP_KEY = "qn3u4wga5xdnddb"
DROPBOX_APP_SECRET = "lqyvaqnyt0awq2j"
DROPBOX_REFRESH_TOKEN = "NEReugJNNk0AAAAAAAAAASxTLjMHAajJw6li26I940g06Vthh9L86TJ7vnxr1k-0"
ACCESS_TOKEN = None  # Updated dynamically

# ✅ Refresh Dropbox token
def refresh_dropbox_token():
    global ACCESS_TOKEN
    url = "https://api.dropbox.com/oauth2/token"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": DROPBOX_REFRESH_TOKEN,
        "client_id": DROPBOX_APP_KEY,
        "client_secret": DROPBOX_APP_SECRET,
    }
    response = requests.post(url, data=data)
    if response.status_code == 200:
        ACCESS_TOKEN = response.json()["access_token"]
    else:
        raise Exception(f"Failed to refresh Dropbox token: {response.json()}")

# ✅ Sanitize filename
def get_clean_filename(url):
    parsed_url = urlparse(url)
    filename = os.path.basename(parsed_url.path)
    filename = unquote(filename).split('?')[0]  # Remove query params
    return filename

# ✅ Stream file to Dropbox
async def stream_file_to_dropbox(update, url, dropbox_path):
    dbx = dropbox.Dropbox(ACCESS_TOKEN)
    chunk_size = 10 * 1024 * 1024  # 10 MB

    # Start the session by uploading the first chunk
    response = requests.get(url, stream=True)
    response.raise_for_status()

    total_size = int(response.headers.get("Content-Length", 0))
    downloaded_size = 0

    file_iter = response.iter_content(chunk_size=chunk_size)

    first_chunk = next(file_iter, None)
    if first_chunk is None:
        raise Exception("Failed to read the file for upload.")

    progress_message = await update.message.reply_text("Progress: Download 0.00%, Upload 0.00%")
    last_update_time = time.time()

    # Start the session
    session_start_result = dbx.files_upload_session_start(first_chunk)
    session_id = session_start_result.session_id
    downloaded_size += len(first_chunk)

    cursor = dropbox.files.UploadSessionCursor(session_id=session_id, offset=len(first_chunk))
    
    while True:
        chunk = next(file_iter, None)
        if chunk is None:
            break
        downloaded_size += len(chunk)

        if time.time() - last_update_time >= 5:
            await progress_message.edit_text(
                f"Progress: Download {downloaded_size / total_size * 100:.2f}%, "
                f"Upload {cursor.offset / total_size * 100:.2f}%"
            )
            last_update_time = time.time()

        dbx.files_upload_session_append_v2(chunk, cursor)
        cursor.offset += len(chunk)

    commit_info = dropbox.files.CommitInfo(path=dropbox_path)
    dbx.files_upload_session_finish(chunk, cursor, commit_info)

    await progress_message.delete()
    await update.message.reply_text(f"✅ File uploaded successfully to Dropbox: {dropbox_path}")

# ✅ Telegram bot
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send me a URL, and I'll upload it to Dropbox!")

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text

    if not url.startswith("http"):
        await update.message.reply_text("Please send a valid URL.")
        return

    await update.message.reply_text("Downloading and uploading the file...")

    try:
        refresh_dropbox_token()
        file_name = get_clean_filename(url)
        dropbox_path = f"/{file_name}"
        await stream_file_to_dropbox(update, url, dropbox_path)

    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

# ✅ Start Telegram bot
async def start_bot():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    await application.run_polling()

# ✅ Run bot in a separate thread
def run_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_bot())

threading.Thread(target=run_bot, daemon=True).start()

# ✅ Run Flask app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True, use_reloader=False)
