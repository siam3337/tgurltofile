import os
from telethon import TelegramClient, events
import yt_dlp
import asyncio
from flask import Flask
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

    # Check the file size and upload accordingly
    file_size = os.path.getsize(file_path)
    max_file_size = 2 * 1024 * 1024 * 1024  # 2GB

    if file_size <= max_file_size:
        await event.respond("Uploading the video...")

        # Upload the file using Telethon
        try:
            await bot.send_file(event.chat_id, file_path, caption="Here is your video!")
        except Exception as e:
            await event.respond(f"Error uploading video: {str(e)}")
    else:
        await event.respond("The video is too large to be sent through Telegram (over 2GB). Please try a smaller video.")
    
    # Clean up the downloaded file
    os.remove(file_path)

# Flask app to respond to health checks
app = Flask(__name__)

@app.route('/')
def index():
    return "Bot is running", 200

# Function to run Flask app in a separate thread
def run_flask():
    app.run(host="0.0.0.0", port=8000)

# Start the Flask app in a separate thread
Thread(target=run_flask).start()

# Start the bot
print("Bot is running...")
bot.run_until_disconnected()
