import os
import time
import uuid  # For generating random names
import telebot
from telebot import apihelper
import requests
from yt_dlp import YoutubeDL
from urllib.parse import quote
import threading  # For running delete in a separate thread
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
import threading
import sys
sys.path.insert(0, '/home/sunpro333/.local/lib/python3.11/site-packages')


API_TOKEN = '6627231473:AAEovoZqjl7ps3ezrF-9Au1iQhiKiWYchWI'  # Replace with your actual (Bot) API token

apihelper.API_URL = "https://tgrasp.co/bot{0}/{1}"  # your address

FLASK_APP_URL = 'https://idoxccz.sufydely.com/downloads/'  # Replace with your Flask app URL
LINK_SHORTENER_API = 'https://api.tinyurl.com/create'  # TinyURL API for shortening links
SHORTENER_API_KEY = 'wA4gS5nUzUA0Vydj5k6gIhK3zEmettu6uG8ruAiZ0yhVQwwW5BK9zjRZKbiH'  # Replace with your TinyURL API key

bot = telebot.TeleBot(API_TOKEN)

# Max file size for direct upload (50 MB)
MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50 MB in bytes

# Global dictionary to store user data (for each chat_id)
user_data = {}

# Auto-delete message function
def auto_delete_message(chat_id, message_id, delay=86400):
    time.sleep(delay)  # Wait for the specified delay before deleting
    try:
        bot.delete_message(chat_id, message_id)
    except Exception as e:
        print(f"Failed to delete message {message_id}: {e}")

# Start command
@bot.message_handler(commands=['start'])
def send_welcome(message):
    # Create a custom keyboard with both buttons
    reply_markup = ReplyKeyboardMarkup(resize_keyboard=True)
    reply_markup.add(
        KeyboardButton("⬇️ Download"),
        KeyboardButton("ℹ️ Supported Sites")
    )

    # Send the welcome message
    bot_msg = bot.reply_to(
        message, 
        "Welcome! Send me a video link from any supported platform (YouTube, Bilibili, etc.) to download.\n\nClick 'ℹ️ Supposed Sites' for List.",
        reply_markup=reply_markup
    )
    
    # Auto-delete the message
    threading.Thread(target=auto_delete_message, args=(message.chat.id, bot_msg.message_id)).start()

@bot.message_handler(func=lambda message: message.text == "ℹ️ Supported Sites")
def send_info_button(message):
    bot_msg = bot.reply_to(
        message, 
        "Supposed Sites List:\n\nClick: https://suncoll.xyz/list.html"
    )
    threading.Thread(target=auto_delete_message, args=(message.chat.id, bot_msg.message_id)).start()

@bot.message_handler(commands=['list'])
def send_info_command(message):
    bot_msg = bot.reply_to(
        message, 
        "Supposed Sites List:\n\nClick: https://suncoll.xyz/list.html"
    )
    threading.Thread(target=auto_delete_message, args=(message.chat.id, bot_msg.message_id)).start()

@bot.message_handler(func=lambda message: message.text == "⬇️ Download")
def send_download_button(message):
    bot_msg = bot.reply_to(
        message,
        "Send me a video link to download. I'll fetch the available formats for you!\n\n Click 'ℹ️ Supposed Sites' for List."
    )
    threading.Thread(target=auto_delete_message, args=(message.chat.id, bot_msg.message_id)).start()

# Example function to auto-delete messages (modify as per your implementation)
def auto_delete_message(chat_id, message_id, delay=3600):
    import time
    time.sleep(delay)  # Wait for the specified delay (default: 10 seconds)
    try:
        bot.delete_message(chat_id, message_id)
    except Exception as e:
        print(f"Error deleting message: {e}")

# Handle video URL
# Your Telegram Channel ID (Use a negative ID for private channels)
LOG_CHANNEL_ID = -1001519297365  # Replace with your channel's ID

@bot.message_handler(func=lambda message: any(protocol in message.text for protocol in ['http://', 'https://']))
def fetch_video_formats(message):
    url = message.text
    chat_id = message.chat.id
    username = message.from_user.username or f"User ID: {chat_id}"
    full_name = message.from_user.full_name or "Unknown Name"

    bot_msg = bot.reply_to(message, "Fetching available video formats...")
    
    # Auto-delete after some time
    threading.Thread(target=auto_delete_message, args=(chat_id, bot_msg.message_id)).start()

    try:
        ydl_opts = {
            'listformats': True,
            'nocolor': True
        }

        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            formats = info_dict.get('formats', [])

        user_data[chat_id] = {'url': url, 'formats': formats}

        # Send log to Telegram channel
        log_message = f"📥 **New Download Request**\n👤 User: [{full_name}](tg://user?id={chat_id})\n🆔 Username: @{username}\n🔗 Link: {url}"
        bot.send_message(LOG_CHANNEL_ID, log_message, parse_mode="Markdown")

        markup = telebot.types.InlineKeyboardMarkup()
        for fmt in formats:
            fmt_id = fmt.get('format_id', 'Unknown')
            resolution = fmt.get('resolution', 'Unknown')
            ext = fmt.get('ext', 'Unknown')
            filesize = fmt.get('filesize')
            tbr = fmt.get('tbr', 0)
            acodec = fmt.get('acodec', 'N/A')
            vcodec = fmt.get('vcodec', 'N/A')

            # Estimate filesize if not available
            if not filesize and tbr:
                duration = info_dict.get('duration', 0)
                if duration:
                    filesize = (tbr * 1000 / 8) * duration

            size_info = f"{filesize / (1024 * 1024):.2f} MB" if filesize else "Size Unknown"
            fmt_info = f"{resolution} | {ext} | {size_info} | V: {vcodec} | A: {acodec}"

            markup.add(telebot.types.InlineKeyboardButton(fmt_info, callback_data=fmt_id))

        if markup.keyboard:
            bot_msg = bot.send_message(chat_id, "Choose video quality:", reply_markup=markup)
            threading.Thread(target=auto_delete_message, args=(chat_id, bot_msg.message_id)).start()
        else:
            bot_msg = bot.send_message(chat_id, "No available formats found. Please try a different video.")
            threading.Thread(target=auto_delete_message, args=(chat_id, bot_msg.message_id)).start()

    except Exception as e:
        bot_msg = bot.reply_to(message, f"Error fetching formats: {str(e)}")
        threading.Thread(target=auto_delete_message, args=(chat_id, bot_msg.message_id)).start()

    except Exception as e:
        bot_msg = bot.reply_to(message, f"Error fetching formats: {str(e)}")
        threading.Thread(target=auto_delete_message, args=(chat_id, bot_msg.message_id)).start()

# Download progress hook function (with message editing)
last_update_time = {}

def progress_hook(d):
    chat_id = d['chat_id']

    if d['status'] == 'downloading':
        now = time.time()

        # Update progress only if 6 seconds have passed since the last update
        if chat_id not in last_update_time or now - last_update_time[chat_id] >= 6:
            percentage = d['_percent_str'].strip()
            speed = d.get('_speed_str', '0 B/s').strip()
            eta = d.get('_eta_str', 'N/A').strip()

            # Update the last update time for the chat
            last_update_time[chat_id] = now

            # Update the Telegram message with progress
            if chat_id in user_data and 'progress_msg_id' in user_data[chat_id]:
                try:
                    bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=user_data[chat_id]['progress_msg_id'],
                        text=f"Downloading: {percentage}\nSpeed: {speed}\nETA: {eta}"
                    )
                except Exception as e:
                    print(f"Failed to edit message: {e}")

    elif d['status'] == 'finished':
        # Notify the user that the download is completed
        if chat_id in user_data and 'progress_msg_id' in user_data[chat_id]:
            try:
                bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=user_data[chat_id]['progress_msg_id'],
                    text="Download completed. Uploading to Telegram..."
                )
            except Exception as e:
                print(f"Failed to edit message: {e}")

@bot.callback_query_handler(func=lambda call: True)
def download_video_or_audio(call):
    chat_id = call.message.chat.id
    message_id = call.message.message_id  # ID of the callback query message
    format_id = call.data

    # Delete the callback query message
    try:
        bot.delete_message(chat_id, message_id)
    except Exception as e:
        print(f"Error deleting callback query message: {e}")

    if chat_id not in user_data or 'url' not in user_data[chat_id]:
        bot_msg = bot.send_message(chat_id, "Sorry, there was an issue retrieving the video URL. Please send the link again.")
        threading.Thread(target=auto_delete_message, args=(chat_id, bot_msg.message_id)).start()
        return

    url = user_data[chat_id]['url']
    formats = user_data[chat_id]['formats']

    selected_format = next((fmt for fmt in formats if fmt.get('format_id') == format_id), None)
    if not selected_format:
        bot_msg = bot.send_message(chat_id, "Selected format not found. Please try again.")
        threading.Thread(target=auto_delete_message, args=(chat_id, bot_msg.message_id)).start()
        return

    # Determine if the selected format is audio-only
    is_audio_only = selected_format.get('vcodec') == 'none'

    # Notify the user that the download is starting
    bot_msg = bot.send_message(chat_id, "Starting download...")
    user_data[chat_id]['progress_msg_id'] = bot_msg.message_id  # Store message ID for editing

    # Start a thread to auto-delete this message after a delay
    threading.Thread(target=auto_delete_message, args=(chat_id, bot_msg.message_id, 3600)).start()

    # Rest of your code... 

    # Generate a random filename (without extension initially)
    random_filename = f"{uuid.uuid4().hex[:8]}"
    output_path = f'downloads/{random_filename}'

    # Configure YoutubeDL options
    if is_audio_only:
        ydl_opts = {
            'format': f'{format_id}',
            'outtmpl': output_path,  # Only provide the base filename, no extension
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'progress_hooks': [lambda d: progress_hook({**d, 'chat_id': chat_id})],
        }
    else:
        output_path += '.mp4'  # Explicitly set extension for video files
        ydl_opts = {
            'format': f'{format_id}+bestaudio/best',  # Chosen quality + best available audio
            'outtmpl': output_path,
            'merge_output_format': 'mp4',
            'progress_hooks': [lambda d: progress_hook({**d, 'chat_id': chat_id})],
        }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # For audio-only, ensure correct file extension
        if is_audio_only:
            output_path_mp3 = f'{output_path}.mp3'
            if not os.path.exists(output_path_mp3) and os.path.exists(output_path):
                os.rename(output_path, output_path_mp3)  # Rename to ensure correct extension
            output_path = output_path_mp3  # Update the path to the renamed file

        file_size = os.path.getsize(output_path)
        if file_size > MAX_UPLOAD_SIZE:
            flask_download_link = f"{FLASK_APP_URL}{quote(os.path.basename(output_path))}"
            short_link = shorten_link(flask_download_link)
            bot.send_message(chat_id, f"The file is too large to upload (over 50 MB). Download it using this link:\n\n `{short_link}`",
                parse_mode="Markdown"
            )
        else:
            if is_audio_only:
                with open(output_path, 'rb') as audio:
                    bot.send_audio(chat_id, audio, title="Audio", performer="Bot", caption="Here is your audio!")
            else:
                with open(output_path, 'rb') as video:
                    bot.send_video(chat_id, video, supports_streaming=True)

    except Exception as e:
        bot.send_message(chat_id, f"Error: {str(e)}")

# Function to shorten a link using TinyURL API (or similar)
def shorten_link(long_url):
    headers = {
        'Authorization': f'Bearer {SHORTENER_API_KEY}',
        'Content-Type': 'application/json',
    }
    data = {"url": long_url}

    try:
        response = requests.post(LINK_SHORTENER_API, json=data, headers=headers)
        if response.status_code == 200:
            response_data = response.json()
            return response_data.get('data', {}).get('tiny_url', long_url)
        return long_url
    except Exception as e:
        print(f"Error shortening link: {e}")
        return long_url


while True:
    try:
        bot.polling(timeout=60, long_polling_timeout=30, none_stop=True)
    except Exception as e:
        print(f"Bot crashed due to {e}. Restarting in 5 seconds...")
        time.sleep(5)
