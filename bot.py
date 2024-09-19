import os
import random
import string
from telethon import TelegramClient, events
import yt_dlp
from flask import Flask, send_from_directory

# Your Telegram API credentials from my.telegram.org
api_id = os.getenv("API_ID")
api_hash = os.getenv("API_HASH")
bot_token = os.getenv("BOT_TOKEN")

# Initialize Flask app
app = Flask(__name__)

# Folder to store downloads
DOWNLOAD_FOLDER = 'downloads'
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# Initialize the bot
bot = TelegramClient('bot', api_id, api_hash).start(bot_token=bot_token)

# yt-dlp options
ydl_opts = {
    'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
    'format': 'best',
}

# Function to download the video using yt-dlp
async def download_video(url):
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=True)
        original_file_path = ydl.prepare_filename(info_dict)
        
        # Rename the file to a random 8-character string
        random_name = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        ext = os.path.splitext(original_file_path)[1]
        new_file_name = random_name + ext
        new_file_path = os.path.join(DOWNLOAD_FOLDER, new_file_name)
        os.rename(original_file_path, new_file_path)
        
        return new_file_name

# Telegram bot event handlers
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
        new_file_name = await download_video(url)
    except Exception as e:
        await event.respond(f"Error downloading video: {str(e)}")
        return

    # Get the file path and size
    file_path = os.path.join(DOWNLOAD_FOLDER, new_file_name)
    file_size = os.path.getsize(file_path)
    max_file_size = 50 * 1024 * 1024  # 50MB

    if file_size <= max_file_size:
        await event.respond("Uploading the video...")

        # Upload the file using Telethon
        try:
            await bot.send_file(event.chat_id, file_path, caption="Here is your video!")
        except Exception as e:
            await event.respond(f"Error uploading video: {str(e)}")
    else:
        # Generate a download link if the file is larger than 50MB
        download_link = f"https://sonic-bot.koyeb.app/download/{new_file_name}"
        await event.respond(f"The video is too large to be sent directly. You can download it from this link: {download_link}")
    
    # Clean up the downloaded file
    # Optionally, you can delete the file after sending the link or leave it for later use

# Flask route to serve downloaded files
@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(DOWNLOAD_FOLDER, filename)

# Start the Flask app on port 8000
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
