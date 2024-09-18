from telethon import TelegramClient, events
from telethon.errors import FloodWaitError
import asyncio
import os
import time
from http.server import SimpleHTTPRequestHandler, HTTPServer
from threading import Thread

# Telegram bot setup
api_id = os.getenv("API_ID")  # You should define API_ID in your environment variables
api_hash = os.getenv("API_HASH")  # You should define API_HASH in your environment variables
bot_token = os.getenv("BOT_TOKEN")  # You should define BOT_TOKEN in your environment variables

if not api_id or not api_hash or not bot_token:
    raise ValueError("Your API ID, Hash, or Bot Token cannot be empty. Ensure environment variables are set correctly.")

client = TelegramClient('bot', api_id, api_hash)

@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.respond('Hello! Send me a URL to upload a file.')

@client.on(events.NewMessage)
async def handle_message(event):
    if event.message.message.startswith('http'):
        await event.respond('URL received. Starting file upload...')
        # Add URL file uploading logic here
        await event.respond('File uploaded successfully!')
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
