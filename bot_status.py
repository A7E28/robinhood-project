# bot_status.py

import psutil
import time
from telethon import events
from credentials import API_ID, API_HASH, BOT_TOKEN

def register_bot_status_feature(client, start_time):
    @client.on(events.NewMessage(pattern='/bot_status'))
    async def bot_status(event):
        # Calculate bot uptime
        uptime = time.time() - start_time
        uptime_str = time.strftime("%H:%M:%S", time.gmtime(uptime))

        # Get CPU and RAM usage
        cpu_percent = psutil.cpu_percent()
        ram_usage = psutil.virtual_memory().percent

        # Calculate ping
        start_ping = time.time()
        message = await event.respond("Calculating ping...")
        end_ping = time.time()
        ping_time = (end_ping - start_ping) * 1000
        await message.edit(f"Bot Uptime: {uptime_str}\n"
                           f"CPU Usage: {cpu_percent}%\n"
                           f"RAM Usage: {ram_usage}%\n"
                           f"Ping: {ping_time:.2f} ms")

        raise events.StopPropagation
