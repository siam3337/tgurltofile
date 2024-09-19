from telethon import TelegramClient, events
from telethon.errors import FloodWaitError
import asyncio
import os
import time
import requests
from http.server import SimpleHTTPRequestHandler, HTTPServer
from threading import Thread

# Telegram bot setup
api_id = os.getenv("API_ID")
api_hash = os.getenv("API_HASH")
bot_token = os.getenv("BOT_TOKEN")

if not api_id or not api_hash or not bot_token:
    raise ValueError("Your API ID, Hash, or Bot Token cannot be empty. Ensure environment variables are set correctly.")

client = TelegramClient('bot', api_id, api_hash)

# Function to handle file download with progress reporting
async def download_file_with_progress(event, url, file_name):
    file_data = requests.get(url, stream=True)
    total_size = int(file_data.headers.get('content-length', 0))
    downloaded_size = 0
    progress_message = await event.respond("Downloading... 0%")  # Initial message for download progress

    with open(file_name, 'wb') as file:
        for chunk in file_data.iter_content(chunk_size=1024 * 1024):  # 1MB chunks
            file.write(chunk)
            downloaded_size += len(chunk)
            download_percentage = (downloaded_size / total_size) * 100

            # Print download progress in terminal
            print(f"Downloading... {download_percentage:.2f}%")

            # Update progress message in the bot, but only if the percentage has changed and is less than 100%
            if download_percentage < 100:
                await progress_message.edit(f"Downloading... {download_percentage:.2f}%")

    # Final update after download completes
    await progress_message.edit(f"Download complete! Starting upload...")

# Event handler for '/start' command
@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.respond('Hello! Send me a URL to upload a file.')

# Event handler for receiving URLs and uploading files
@client.on(events.NewMessage)
async def handle_message(event):
    if event.message.message.startswith('http'):
        await event.respond('URL received. Starting file download...')
        
        url = event.message.message  # Get the URL from the message
        file_name = url.split('/')[-1]  # Extract a file name from the URL
        
        try:
            # Download the file from the URL with progress reporting
            await download_file_with_progress(event, url, file_name)

            # Send the file to the chat
            await client.send_file(event.chat_id, file_name)

            # Notify user of upload completion
            await event.respond('File uploaded successfully!')
            
            # Delete the file after sending
            os.remove(file_name)

        except Exception as e:
            await event.respond(f"An error occurred: {str(e)}")
    else:
        await event.respond('Please send a valid URL.')

# Function to handle FloodWaitError
async def start_bot():
    try:
        await client.start(bot_token=bot_token)
        print("Bot started successfully!")
        await client.run_until_disconnected()
    except FloodWaitError as e:
        print(f"FloodWaitError: Waiting for {e.seconds} seconds.")
        time.sleep(e.seconds)  # Wait for the required time
        await start_bot()  # Retry after the wait time

# Function to run the simple health check server
def run_health_check_server():
    server = HTTPServer(('0.0.0.0', 8000), SimpleHTTPRequestHandler)
    print("Health check server is running on port 8000.")
    server.serve_forever()

# Main function
async def main():
    # Start the health check server in a separate thread
    server_thread = Thread(target=run_health_check_server)
    server_thread.daemon = True
    server_thread.start()

    # Start the Telegram bot
    await start_bot()

if __name__ == '__main__':
    # Run the asyncio event loop
    asyncio.run(main())
