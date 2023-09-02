import telebot
import time
import psutil
import platform
import timeit

# Function to generate a text-based progress bar
def progress_bar(percentage):
    filled_blocks = int(round(percentage / 10))
    empty_blocks = 10 - filled_blocks
    return "▓" * filled_blocks + "░" * empty_blocks

def register_bot_status_feature(bot, start_time):
    @bot.message_handler(commands=['bot_status'])
    def bot_status(message):
        # Calculate bot uptime
        uptime = time.time() - start_time
        uptime_str = time.strftime("%H:%M:%S", time.gmtime(uptime))

        # Get system information
        system_info = platform.system() + ' ' + platform.release()

        # Get CPU information
        cpu_info = platform.processor()

        # Get RAM information
        ram_info = psutil.virtual_memory()
        total_ram = round(ram_info.total / (1024 ** 3), 2)  # Convert to GB
        ram_usage = round(ram_info.percent, 1)

        # Get disk information
        disk_info = psutil.disk_usage('/')
        total_disk = round(disk_info.total / (1024 ** 3), 2)  # Convert to GB

        # Get CPU and RAM usage
        cpu_percent = psutil.cpu_percent()

        # Calculate ping using timeit
        ping_time = timeit.timeit(lambda: bot.send_message(message.chat.id, "Ping"), number=1) * 1000

        # Create graphical representations for CPU and RAM usage
        cpu_progress = progress_bar(cpu_percent)
        ram_progress = progress_bar(ram_usage)

        # Compose the response with the graphical representations
        response = (
            f"🤖 Bot Uptime: {uptime_str}\n"
            f"🖥️ System: {system_info}\n"
            f"🔍 Total RAM: {total_ram} GB\n"
            f"💻 CPU: {cpu_info}\n"
            f"💽 Total Disk: {total_disk} GB\n"
            f"📊 CPU Usage:\n"
            f"{cpu_progress} {cpu_percent}%\n"
            f"🔵 RAM Usage:\n"
            f"{ram_progress} {ram_usage}%\n"
            f"📶 Ping: {ping_time:.2f} ms"
        )

        bot.send_message(message.chat.id, response)
