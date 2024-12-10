import os
import telebot
import requests
import dropbox
import libtorrent as lt
import time
from flask import Flask
import threading

# Load sensitive credentials from environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")

# Validate environment variables
if not TELEGRAM_BOT_TOKEN or not DROPBOX_ACCESS_TOKEN:
    raise Exception("Environment variables TELEGRAM_BOT_TOKEN and DROPBOX_ACCESS_TOKEN are required!")

# Initialize Telegram bot and Dropbox client
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

CHUNK_SIZE = 4 * 1024 * 1024  # 4 MB

# Flask app for health checks
app = Flask(__name__)

@app.route("/health")
def health():
    return "OK", 200

def start_flask():
    app.run(host="0.0.0.0", port=8000)

# (Rest of the code remains unchanged from the previously provided code)
# Includes `stream_upload_to_dropbox`, `stream_torrent_to_dropbox`, 
# and all Telegram bot handlers.

# Function to upload a file to Dropbox with progress updates
def stream_upload_to_dropbox(url, dropbox_path, chat_id):
    with requests.get(url, stream=True) as response:
        if response.status_code != 200:
            raise Exception(f"Failed to download URL: {response.status_code}")

        file_size = int(response.headers.get("Content-Length", 0))
        uploaded_size = 0
        upload_session_start_result = None
        file_iter = response.iter_content(CHUNK_SIZE)

        try:
            # Start the upload session
            chunk = next(file_iter)
            upload_session_start_result = dbx.files_upload_session_start(chunk)
            cursor = dropbox.files.UploadSessionCursor(
                session_id=upload_session_start_result.session_id,
                offset=len(chunk),
            )
            uploaded_size += len(chunk)
            bot.send_message(chat_id, f"Uploaded: {uploaded_size / file_size * 100:.2f}%")

            # Upload remaining chunks
            for chunk in file_iter:
                dbx.files_upload_session_append_v2(chunk, cursor)
                cursor.offset += len(chunk)
                uploaded_size += len(chunk)
                bot.send_message(chat_id, f"Uploaded: {uploaded_size / file_size * 100:.2f}%")

            # Finish the upload
            dbx.files_upload_session_finish(
                b"",
                cursor,
                dropbox.files.CommitInfo(path=dropbox_path),
            )
        except StopIteration:
            pass

    # Get Dropbox shared link
    shared_link = dbx.sharing_create_shared_link_with_settings(dropbox_path).url

    # Modify the link to the desired format
    modified_link = shared_link.replace(
        "www.dropbox.com", "dl.dropboxusercontent.com"
    ).replace("dl=0", "dl=1")

    return modified_link

# Function to handle torrent upload to Dropbox
def stream_torrent_to_dropbox(magnet_link, dropbox_folder, chat_id):
    session = lt.session()
    session.listen_on(6881, 6891)
    params = {"save_path": "./downloads"}
    handle = lt.add_magnet_uri(session, magnet_link, params)

    while not handle.has_metadata():
        time.sleep(1)

    torrent_info = handle.get_torrent_info()
    file_list = torrent_info.files()
    total_size = sum(f.size for f in file_list)

    bot.send_message(chat_id, f"Starting torrent download: {total_size / (1024 * 1024):.2f} MB")

    for f in file_list:
        file_path = f.path
        full_path = os.path.join(params["save_path"], file_path)

        while not os.path.exists(full_path):
            time.sleep(1)

        # Stream file to Dropbox
        dropbox_path = f"{dropbox_folder}/{os.path.basename(file_path)}"
        shared_link = stream_upload_to_dropbox(full_path, dropbox_path, chat_id)

        return f"Torrent successfully uploaded to Dropbox: {shared_link}"

# Telegram bot handlers
@bot.message_handler(commands=["start"])
def send_welcome(message):
    bot.reply_to(message, "Send me a video URL or a torrent magnet link, and I'll upload it to Dropbox!")

@bot.message_handler(func=lambda message: message.text.startswith("http"))
def handle_url(message):
    url = message.text
    try:
        bot.reply_to(message, "Uploading URL directly to Dropbox...")
        file_name = url.split("/")[-1]
        dropbox_path = f"/{file_name}"
        shared_link = stream_upload_to_dropbox(url, dropbox_path, message.chat.id)
        bot.reply_to(message, f"Upload complete! Download link: {shared_link}")
    except Exception as e:
        bot.reply_to(message, f"Error: {e}")

@bot.message_handler(func=lambda message: message.text.startswith("magnet:?"))
def handle_magnet(message):
    magnet_link = message.text
    try:
        bot.reply_to(message, "Uploading torrent to Dropbox...")
        response = stream_torrent_to_dropbox(magnet_link, "/Torrent_Files", message.chat.id)
        bot.reply_to(message, response)
    except Exception as e:
        bot.reply_to(message, f"Error: {e}")

@bot.message_handler(content_types=["document"])
def handle_torrent_file(message):
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        # Save .torrent file locally
        torrent_file_path = f"./{message.document.file_name}"
        with open(torrent_file_path, "wb") as f:
            f.write(downloaded_file)

        # Parse .torrent file
        bot.reply_to(message, "Uploading torrent to Dropbox...")
        response = stream_torrent_to_dropbox(torrent_file_path, "/Torrent_Files", message.chat.id)
        bot.reply_to(message, response)

        # Clean up
        os.remove(torrent_file_path)
    except Exception as e:
        bot.reply_to(message, f"Error: {e}")

# Run Flask server in a thread
threading.Thread(target=start_flask).start()

# Start the Telegram bot
print("Bot is running...")
bot.infinity_polling()
