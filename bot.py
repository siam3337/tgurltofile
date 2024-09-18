from telethon import TelegramClient, events
import os
import threading
from http.server import SimpleHTTPRequestHandler, HTTPServer

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

# Function to run the Telegram bot
def run_telegram_bot():
    client.run_until_disconnected()

# Simple HTTP server for health check
class HealthCheckHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'OK')

def run_health_check_server():
    server = HTTPServer(('0.0.0.0', 8000), HealthCheckHandler)
    server.serve_forever()

# Run the bot and web server concurrently
if __name__ == "__main__":
    # Start the Telegram bot in a separate thread
    bot_thread = threading.Thread(target=run_telegram_bot)
    bot_thread.start()

    # Start the health check server
    run_health_check_server()
