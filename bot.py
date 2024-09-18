from telethon import TelegramClient, events
import os

# Replace these with your own API credentials
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
            # Here you could add logic to process or upload the file
            await event.respond('File upload completed.')
        else:
            await event.respond('File size exceeds 2GB limit.')
    else:
        await event.respond('Please send a file.')

client.start()
client.run_until_disconnected()
