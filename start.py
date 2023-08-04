#start.py
from telethon import events

def register_start_feature(client):
    @client.on(events.NewMessage(pattern='/start'))
    async def start(event):
        await event.respond("Hello! I am your Telegram bot!")
        raise events.StopPropagation
