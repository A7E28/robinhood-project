import time
import psutil
import platform
import os
import subprocess
from telethon import events

# Function to generate a text-based progress bar
def progress_bar(percentage):
    filled_blocks = int(round(percentage / 10))
    empty_blocks = 10 - filled_blocks
    return "▓" * filled_blocks + "░" * empty_blocks

def get_cpu_model():
    try:
        if platform.system() == "Windows":
            return platform.processor()
        else:
            # For Linux or other platforms, use subprocess to call lscpu if available
            model_name = subprocess.check_output("lscpu | grep 'Model name' | awk -F ': ' '{print $2}'", shell=True, text=True).strip()
            return model_name
    except Exception as e:
        print("Error getting CPU model:", e)
        return "Unknown CPU"

def register_bot_status_feature(client, start_time):
    @client.on(events.NewMessage(pattern='/bot_status'))
    async def bot_status(event):
        # Calculate bot uptime
        uptime = time.time() - start_time
        uptime_str = time.strftime("%H:%M:%S", time.gmtime(uptime))

        # Get system information
        system_info = f"🖥️ System: {platform.system()} {platform.release()}"

        # Get total RAM
        total_ram = psutil.virtual_memory().total
        total_ram_str = f"🔍 Total RAM: {total_ram // (1024 ** 3)} GB"

        # Get CPU information
        cpu_model = get_cpu_model()
        cpu_string = f"💻 CPU: {cpu_model}, {os.cpu_count()} Thread"

        # Get total disk usage
        total_disk = psutil.disk_usage('/').total
        total_disk_str = f"💽 Total Disk: {total_disk // (1024 ** 3)} GB"

        # Get CPU and RAM usage
        cpu_percent = psutil.cpu_percent()
        ram_usage = psutil.virtual_memory().percent

        # Calculate ping
        start_ping = time.time()
        message = await event.respond("⏳ Calculating ping...")
        end_ping = time.time()
        ping_time = (end_ping - start_ping) * 1000

        # Create graphical representations for CPU and RAM usage
        cpu_progress = progress_bar(cpu_percent)
        ram_progress = progress_bar(ram_usage)

        # Compose the response with the gathered information
        response = (
            f"🤖 Bot Uptime: {uptime_str}\n"
            f"{system_info}\n"
            f"{total_ram_str}\n"
            f"{cpu_string}\n"
            f"{total_disk_str}\n"
            f"📊 CPU Usage:\n"
            f"{cpu_progress} {cpu_percent}%\n"
            f"🔵 RAM Usage:\n"
            f"{ram_progress} {ram_usage}%\n"
            f"📶 Ping: {ping_time:.2f} ms"
        )

        await message.edit(response)

        raise events.StopPropagation
