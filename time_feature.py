#time_feature.py
import datetime
from telethon import events

def register_time_feature(client):
    @client.on(events.NewMessage(pattern='/time'))
    async def show_time(event):
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        await event.respond(f"Current date and time: {current_time}")
        raise events.StopPropagation
