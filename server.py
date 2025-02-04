import threading
import asyncio
import io
import os
import time
import requests
import dropbox
from urllib.parse import urlparse, unquote
from flask import Flask
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# Flask App
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!"

# Telegram bot token
TELEGRAM_BOT_TOKEN = "5876860733:AAFAPmqGHd0NDI-tatG8FboMuMEwE9dOGYA"

# Dropbox Credentials
DROPBOX_APP_KEY = "qn3u4wga5xdnddb"
DROPBOX_APP_SECRET = "lqyvaqnyt0awq2j"
DROPBOX_REFRESH_TOKEN = "NEReugJNNk0AAAAAAAAAASxTLjMHAajJw6li26I940g06Vthh9L86TJ7vnxr1k-0"
ACCESS_TOKEN = None  # Updated dynamically

# Refresh Dropbox token
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

# Modify Dropbox URL
def modify_dropbox_url(original_url, mode="download"):
    modified_url = original_url.replace("www.dropbox.com", "dl.dropboxusercontent.com")
    if mode == "download":
        return modified_url.replace("dl=0", "dl=1") if "dl=" in modified_url else modified_url + "&dl=1"
    elif mode == "stream":
        return modified_url.replace("dl=1", "dl=0") if "dl=" in modified_url else modified_url + "&dl=0"

# Shorten URLs
def shorten_url_with_tinyurl(long_url):
    api_url = f"https://tinyurl.com/api-create.php?url={long_url}"
    response = requests.get(api_url)
    if response.status_code == 200:
        return response.text
    return long_url  

# Clean filename
def get_clean_filename(url):
    parsed_url = urlparse(url)
    filename = os.path.basename(parsed_url.path)
    filename = unquote(filename)
    filename = filename.split('?')[0]  
    return filename

# Stream file to Dropbox
async def stream_file_to_dropbox(update, url, dropbox_path):
    dbx = dropbox.Dropbox(ACCESS_TOKEN)
    chunk_size = 10 * 1024 * 1024  

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

    shared_link = dbx.sharing_create_shared_link_with_settings(dropbox_path)
    
    direct_download_link = modify_dropbox_url(shared_link.url, mode="download")
    live_stream_link = modify_dropbox_url(shared_link.url, mode="stream")

    short_direct_download = shorten_url_with_tinyurl(direct_download_link)
    short_live_stream = shorten_url_with_tinyurl(live_stream_link)

    return short_direct_download, short_live_stream

# Telegram Commands
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send me a URL, and I'll upload the file to Dropbox for you!")

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
        short_direct_download, short_live_stream = await stream_file_to_dropbox(update, url, dropbox_path)

        await update.message.reply_text(
            f"✅ **File Uploaded Successfully!**\n\n"
            f"📥 **Direct Download Link:**\n{short_direct_download}\n\n"
            f"▶️ **Live Stream Link:**\n{short_live_stream}"
        )

    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

# Start Telegram Bot
async def start_bot():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    
    print("Bot is running...")
    await application.run_polling()

def run_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_bot())

if __name__ == "__main__":
    # Start the bot in a separate thread
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()

    # Start Flask Server
    print("Starting Flask server on port 8000...")
    app.run(host="0.0.0.0", port=8000, debug=False, threaded=True)
