from telethon import TelegramClient, events
from telethon.errors import FloodWaitError
from telethon.tl.types import DocumentAttributeFilename
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

# Chunk size in bytes (example: 1 MB chunks)
CHUNK_SIZE = 1024 * 1024

@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.respond('Hello! Send me a URL to upload a file.')

@client.on(events.NewMessage)
async def handle_message(event):
    if event.message.message.startswith('http'):
        await event.respond('URL received. Starting file upload...')
        
        url = event.message.message  # Get the URL from the message
        file_name = url.split('/')[-1]  # Extract a file name from the URL
        
        try:
            # Download the file from the URL in chunks
            file_data = requests.get(url, stream=True)
            if file_data.status_code == 200:
                total_size = int(file_data.headers.get('content-length', 0))
                downloaded_size = 0
                with open(file_name, 'wb') as file:
                    for chunk in file_data.iter_content(chunk_size=CHUNK_SIZE):
                        file.write(chunk)
                        downloaded_size += len(chunk)
                        print(f"Downloaded {downloaded_size}/{total_size} bytes")
                
                # Send the file to the chat in chunks
                await send_file_in_chunks(event.chat_id, file_name)

                await event.respond('File uploaded successfully!')
                
                # Delete the file after sending
                os.remove(file_name)
            else:
                await event.respond(f"Failed to download the file. HTTP Status: {file_data.status_code}")
        
        except Exception as e:
            await event.respond(f"An error occurred: {str(e)}")
    else:
        await event.respond('Please send a valid URL.')

# Function to send the file in chunks
async def send_file_in_chunks(chat_id, file_path):
    total_size = os.path.getsize(file_path)
    file_name = os.path.basename(file_path)

    # Send the file using Telethon's upload functionality
    with open(file_path, 'rb') as file:
        uploaded_size = 0
        while uploaded_size < total_size:
            # Calculate how much to upload in this iteration
            chunk = file.read(CHUNK_SIZE)
            if not chunk:
                break

            # Upload the chunk as part of the file
            await client.send_file(
                chat_id,
                file,
                file_name=file_name,
                force_document=True,
                attributes=[DocumentAttributeFilename(file_name)],
                thumb=None,
                caption=f"Uploading chunk... {uploaded_size / total_size * 100:.2f}% complete"
            )
            uploaded_size += len(chunk)
            print(f"Uploaded {uploaded_size}/{total_size} bytes")

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
