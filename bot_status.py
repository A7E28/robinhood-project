import psutil
import time
from telethon import events
from credentials import API_ID, API_HASH, BOT_TOKEN

# Function to generate a text-based progress bar
def progress_bar(percentage):
    filled_blocks = int(round(percentage / 10))
    empty_blocks = 10 - filled_blocks
    return "▓" * filled_blocks + "░" * empty_blocks

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

        # Create graphical representations for CPU and RAM usage
        cpu_progress = progress_bar(cpu_percent)
        ram_progress = progress_bar(ram_usage)

        # Compose the response with the graphical representations
        response = (
            f"Bot Uptime: {uptime_str}\n"
            f"CPU Usage: {cpu_percent}%\n"
            f"{cpu_progress} {cpu_percent}%\n"
            f"RAM Usage: {ram_usage}%\n"
            f"{ram_progress} {ram_usage}%\n"
            f"Ping: {ping_time:.2f} ms"
        )

        await message.edit(response)

        raise events.StopPropagation
