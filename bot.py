from telethon import TelegramClient, events
import os
import asyncio
from http.server import SimpleHTTPRequestHandler, HTTPServer
from threading import Thread

# Telegram bot setup
api_id = '22146262'
api_hash = 'f7bf31f583cf386f0d3d7732727a18d7'
bot_token = '6627231473:AAEovoZqjl7ps3ezrF-9Au1iQhiKiWYchWI'

client = TelegramClient('bot', api_id, api_hash).start(bot_token=bot_token)

@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.respond('Send me a file, and I will upload it for you!')

@client.on(events.NewMessage)
async def handle_file(event):
    if event.message.file:
        file = await event.message.download_media()
        file_size = os.path.getsize(file)
        if file_size <= 2 * 1024 * 1024 * 1024:  # Check if file size <= 2GB
            await event.respond('File received! Uploading...')
            # Add your file processing logic here
            await event.respond('File upload completed.')
        else:
            await event.respond('File size exceeds 2GB limit.')
    else:
        await event.respond('Please send a file.')

# Function to run the simple health check server
def run_health_check_server():
    server = HTTPServer(('0.0.0.0', 8000), SimpleHTTPRequestHandler)
    server.serve_forever()

# Main entry point
async def main():
    # Start the health check server in a separate thread
    server_thread = Thread(target=run_health_check_server)
    server_thread.daemon = True
    server_thread.start()

    # Start the Telegram bot and run it until disconnected
    await client.run_until_disconnected()

if __name__ == '__main__':
    # Run the asyncio event loop
    asyncio.run(main())
