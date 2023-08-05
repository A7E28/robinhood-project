import telebot
import time
import psutil

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

        # Get CPU and RAM usage
        cpu_percent = psutil.cpu_percent()
        ram_usage = psutil.virtual_memory().percent

        # Calculate ping
        start_ping = time.time()
        sent_message = bot.send_message(message.chat.id, "Calculating ping...")
        end_ping = time.time()
        ping_time = (end_ping - start_ping) * 1000

        # Create graphical representations for CPU and RAM usage
        cpu_progress = progress_bar(cpu_percent)
        ram_progress = progress_bar(ram_usage)

        # Compose the response with the graphical representations
        response = (
            f"Bot Uptime: {uptime_str}\n"
            f"CPU Usage:\n"
            f"{cpu_progress} {cpu_percent}%\n"
            f"RAM Usage:\n"
            f"{ram_progress} {ram_usage}%\n"
            f"Ping: {ping_time:.2f} ms"
        )

        bot.edit_message_text(response, message.chat.id, sent_message.message_id)
