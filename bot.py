import os
from telethon import TelegramClient, events
import yt_dlp
import asyncio
from flask import Flask, send_from_directory
from threading import Thread

# Your Telegram API credentials from my.telegram.org
api_id = os.getenv("API_ID")
api_hash = os.getenv("API_HASH")
bot_token = os.getenv("BOT_TOKEN")

# Initialize the bot
bot = TelegramClient('bot', api_id, api_hash).start(bot_token=bot_token)

# yt-dlp options
ydl_opts = {
    'outtmpl': 'downloads/%(title)s.%(ext)s',
    'format': 'best',
}

# Function to download the video using yt-dlp
async def download_video(url):
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=True)
        file_path = ydl.prepare_filename(info_dict)
        return file_path

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.respond("Hello! Send me a video link and I'll download it for you!")

@bot.on(events.NewMessage)
async def handle_video(event):
    url = event.message.message.strip()

    # Checking if the message is a valid URL
    if not url.startswith('http'):
        await event.respond("Please send a valid URL.")
        return

    await event.respond("Downloading... Please wait...")

    # Download the video
    try:
        file_path = await download_video(url)
    except Exception as e:
        await event.respond(f"Error downloading video: {str(e)}")
        return

    # Check the file size
    file_size = os.path.getsize(file_path)
    max_file_size = 50 * 1024 * 1024  # 50 MB

    if file_size <= max_file_size:
        await event.respond("Uploading the video...")

        # Upload the file using Telethon
        try:
            await bot.send_file(event.chat_id, file_path, caption="Here is your video!")
        except Exception as e:
            await event.respond(f"Error uploading video: {str(e)}")
    else:
        # Create a download link for large files
        download_link = f"https://sonic-bot.koyeb.app/download/{os.path.basename(file_path)}"
        await event.respond(f"The video is too large to be sent directly. You can download it from this link: {download_link}")
    
    # Clean up the downloaded file
    os.remove(file_path)

# Flask app to respond to health checks and provide downloads
app = Flask(__name__)

@app.route('/')
def index():
    return "Bot is running", 200

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory('downloads', filename, as_attachment=True)

# Function to run Flask app in a separate thread
def run_flask():
    app.run(host="0.0.0.0", port=8000)

# Start the Flask app in a separate thread
Thread(target=run_flask).start()

# Start the bot
print("Bot is running...")
bot.run_until_disconnected()
