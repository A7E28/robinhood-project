import telebot
import ping3
import psutil

# Function to generate a text-based progress bar
def progress_bar(percentage):
    filled_blocks = int(round(percentage / 10))
    empty_blocks = 10 - filled_blocks
    return "▓" * filled_blocks + "░" * empty_blocks

def get_response_time(device_line):
    try:
        device_name, ip = device_line.strip().split(', ')
        response_time = ping3.ping(ip, timeout=2, unit='ms')
        if response_time is not None:
            return f"{device_name} ({ip}): {response_time:.2f} ms", True
        else:
            return f"{device_name} ({ip}): Offline", False
    except ping3.PingError as e:
        return f"{device_name} ({ip}): Host unreachable or invalid IP", False
    except ping3.Timeout as e:
        return f"{device_name} ({ip}): Request timed out", False

def register_status_feature(bot):
    @bot.message_handler(commands=['status'])
    def check_status(message):
        with open('device.txt', 'r') as file:
            device_lines = file.readlines()

        online_msg = "Online Devices:\n"
        offline_msg = ""

        for line in device_lines:
            response_time, is_online = get_response_time(line)
            if is_online:
                online_msg += f"{response_time}\n"
            else:
                offline_msg += f"{response_time}\n"

        response_msg = online_msg
        if offline_msg:
            response_msg += "\nOffline Devices:\n" + offline_msg

        bot.reply_to(message, response_msg)
