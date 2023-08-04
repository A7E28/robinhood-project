from telethon import TelegramClient, events
import asyncio
import subprocess
from datetime import datetime, timedelta
import pandas as pd
import xlsxwriter
import psutil

# Telegram API credentials
API_ID = 27024327
API_HASH = '669bdeddb70a2961aafcad641528aead'
BOT_TOKEN = '6233443371:AAEMU3svmTajA0wnLEKjQHa4cXmmbwtfFHY'
CHAT_ID = 1436979843

# IP addresses and their corresponding names
IP_NAME_MAPPING = {
    "8.8.8.8": "Google DNS",
    "192.168.0.1": "Router",
    "192.168.0.127": "Mobile",
}

# Initialize the Telegram client
client = TelegramClient('status_bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# Dictionary to store the online status of devices
online_status = {}

# Dictionary to store the offline status of devices
offline_status = {}

# Dictionary to store the offline data (offline time and duration) of devices
offline_data = {ip: {'events': [], 'durations': []} for ip in IP_NAME_MAPPING}

# Global variable to store the start time of the bot
start_time = None

# Global variable to store the ping response time
PING_RESPONSE_TIME = None


async def ping_ip(ip):
    """
    Pings an IP address and returns the response time in milliseconds if successful, else returns None.
    """
    try:
        result = await asyncio.to_thread(subprocess.run, ['ping', '-n', '1', '-w', '2000', ip], capture_output=True)
        response = result.stdout.decode()
        if 'Reply from' in response:
            response_time = int(response.split("time=")[1].split("ms")[0])
            return response_time
        else:
            return None
    except Exception:
        return None


async def send_online_devices_status():
    """
    Checks the online status of devices and sends the list of online devices to the chat.
    """
    online_devices = []

    for ip, name in IP_NAME_MAPPING.items():
        response_time = await ping_ip(ip)

        if response_time is not None:
            online_devices.append(f"{name} ({ip}) - Response Time: {response_time} ms")
            online_status[ip] = response_time
            # Remove from offline_status if previously offline
            offline_status.pop(ip, None)

    if online_devices:
        online_message = "Online Devices:\n\n" + "\n".join(online_devices)
        await client.send_message(CHAT_ID, online_message)


async def send_offline_devices_status(ip):
    """
    Checks the offline status of a specific device and sends the offline message to the chat.
    """
    offline_devices = []
    name = IP_NAME_MAPPING.get(ip, "Unknown Device")

    response_time = await ping_ip(ip)

    if response_time is None:
        if ip not in offline_status:
            # Device was previously online, set offline time
            offline_data[ip]['events'].append(datetime.now())

        offline_devices.append(f"{name} ({ip})")
        offline_status[ip] = True
        # Remove from online_status if previously online
        online_status.pop(ip, None)

    if offline_devices:
        offline_message = "Offline Devices:\n\n" + "\n".join(offline_devices)
        await client.send_message(CHAT_ID, offline_message)


async def send_offline_devices_data():
    """
    Sends the offline data (offline time and duration) of devices to the chat.
    """
    offline_data_message = "Offline Device Data:\n\n"
    for ip, data in offline_data.items():
        name = IP_NAME_MAPPING.get(ip, "Unknown Device")
        offline_events = data['events']
        offline_durations = data['durations']

        for i, offline_time in enumerate(offline_events):
            duration = datetime.now() - offline_time
            online_time = offline_time + duration
            offline_durations.append(duration)
            offline_data_message += f"{name} ({ip})\n"
            offline_data_message += f"Offline Time: {offline_time.strftime('%H:%M')}\n"
            offline_data_message += f"Online Time: {online_time.strftime('%H:%M')}\n"
            offline_data_message += f"Offline Duration: {str(duration).split('.')[0]}\n\n"

    if offline_data_message != "Offline Device Data:\n\n":
        await client.send_message(CHAT_ID, offline_data_message)


async def generate_report_sheet():
    """
    Generates an Excel report sheet containing the offline data (offline time and duration) of devices.
    """
    offline_devices_data = []
    columns = ['Device', 'IP', 'Offline Time', 'Online Time', 'Offline Duration']

    for ip, data in offline_data.items():
        name = IP_NAME_MAPPING.get(ip, "Unknown Device")
        offline_events = data['events']
        offline_durations = data['durations']

        for i, offline_time in enumerate(offline_events):
            duration = datetime.now() - offline_time
            online_time = offline_time + duration
            offline_durations.append(duration)

            offline_devices_data.append(
                [name, ip, offline_time.strftime('%H:%M'), online_time.strftime('%H:%M'), str(duration).split('.')[0]])

    df = pd.DataFrame(offline_devices_data, columns=columns)

    # Create a new Excel workbook using xlsxwriter
    file_name = "offline_report.xlsx"
    writer = pd.ExcelWriter(file_name, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Offline Data')

    # Access the underlying XlsxWriter workbook and worksheet
    workbook = writer.book
    sheet = writer.sheets['Offline Data']

    # Adjust column widths for better readability
    for idx, column in enumerate(df.columns):
        column_width = max(df[column].astype(str).str.len().max(), len(column))
        sheet.set_column(idx, idx, column_width + 2)

    # Apply alignment to center the data in cells
    center_alignment = workbook.add_format({'align': 'center', 'valign': 'vcenter'})
    for row_num, row_data in enumerate(df.values):
        for col_num, cell_value in enumerate(row_data):
            sheet.write(row_num + 1, col_num, cell_value, center_alignment)

    writer.close()  # Save and close the Excel file

    # Send the generated Excel file to the chat
    await client.send_file(CHAT_ID, file_name)


async def check_and_send_devices_status():
    """
    Periodically checks the online status of devices and sends status messages to the chat.
    """
    while True:
        for ip, name in IP_NAME_MAPPING.items():
            if ip in online_status:
                # Device is already marked as online, check if it is still online
                response_time = await ping_ip(ip)
                if response_time is None:
                    # Device is offline now, send offline status message
                    await send_offline_devices_status(ip)
            else:
                # Device is not marked as online, check if it is online now
                response_time = await ping_ip(ip)
                if response_time is not None:
                    # Device is online now, send online status message
                    online_status[ip] = response_time
                    online_message = f"{name} ({ip}) - Response Time: {response_time} ms"
                    await client.send_message(CHAT_ID, online_message)

                    # Check if the device was previously offline
                    if ip in offline_status:
                        await client.send_message(CHAT_ID, f"{name} ({ip}) is online now.")
                        # Remove from offline_status since it's online now
                        offline_status.pop(ip, None)

        await asyncio.sleep(5)  # Wait for 5 seconds before checking again


async def get_bot_status():
    """
    Sends the bot status (CPU usage, RAM usage, uptime, and ping) to the chat.
    """
    global start_time, PING_RESPONSE_TIME

    # Initialize the start time if it's not set
    if start_time is None:
        start_time = datetime.now()

    # Get system information
    cpu_usage = psutil.cpu_percent(interval=1)
    ram_usage = psutil.virtual_memory().percent

    # Get uptime in a human-readable format
    uptime_seconds = int((datetime.now() - start_time).total_seconds())
    uptime_str = str(timedelta(seconds=uptime_seconds))

    # Perform an internal ping from Telegram to the bot
    PING_RESPONSE_TIME = None
    await client.send_message(CHAT_ID, "Pinging...")
    start_ping_time = datetime.now()
    await client.get_me()  # Send a request to Telegram to measure ping
    end_ping_time = datetime.now()
    PING_RESPONSE_TIME = (end_ping_time - start_ping_time).total_seconds() * 1000

    if PING_RESPONSE_TIME is not None:
        status_message = (
            f"Bot Status:\n\n"
            f"CPU Usage: {cpu_usage:.1f}%\n"
            f"RAM Usage: {ram_usage:.1f}%\n"
            f"Uptime: {uptime_str}\n"
            f"Ping: {PING_RESPONSE_TIME:.2f} ms"
        )
    else:
        status_message = (
            f"Bot Status:\n\n"
            f"CPU Usage: {cpu_usage:.1f}%\n"
            f"RAM Usage: {ram_usage:.1f}%\n"
            f"Uptime: {uptime_str}\n"
            f"Ping: N/A"
        )
    await client.send_message(CHAT_ID, status_message)


async def ping_response_handler():
    """
    Handler for the /ping command that the bot sends to itself to measure the ping response time.
    """
    global PING_RESPONSE_TIME
    if PING_RESPONSE_TIME is None:
        end_time = datetime.now()
        PING_RESPONSE_TIME = (end_time - start_time).total_seconds() * 1000

# Function to reset the bot
def reset_bot():
    """
    Resets all dictionaries and variables to their initial state.
    """
    global online_status, offline_status, offline_data, start_time, PING_RESPONSE_TIME
    online_status = {}
    offline_status = {}
    offline_data = {ip: {'events': [], 'durations': []} for ip in IP_NAME_MAPPING}
    start_time = None
    PING_RESPONSE_TIME = None

@client.on(events.NewMessage(pattern='/status'))
async def get_status(event):
    """
    Handler for the /status command to get the current online and offline status of all devices.
    """
    # Get the current online status of all devices
    await send_online_devices_status()

    # Get the offline status of devices and send them as well
    offline_devices = [f"{name} ({ip})" for ip, name in IP_NAME_MAPPING.items() if ip in offline_status]
    if offline_devices:
        offline_message = "Offline Devices:\n\n" + "\n".join(offline_devices)
        await client.send_message(CHAT_ID, offline_message)


@client.on(events.NewMessage(pattern='/time'))
async def get_offline_data(event):
    """
    Handler for the /time command to get and send the offline data of devices.
    """
    await send_offline_devices_data()


@client.on(events.NewMessage(pattern='/report_sheet'))
async def get_report_sheet(event):
    """
    Handler for the /report_sheet command to generate and send the Excel report sheet.
    """
    await generate_report_sheet()


@client.on(events.NewMessage(pattern='/bot_status'))
async def bot_status(event):
    """
    Handler for the /bot_status command to get and send the bot status.
    """
    await get_bot_status()

# Handler for /restart_bot command
@client.on(events.NewMessage(pattern='/restart_bot'))
async def restart_bot(event):
    """
    Handler for the /restart_bot command to reset the bot.
    """
    reset_bot()
    await client.send_message(CHAT_ID, "Bot has been reset. Starting from the beginning.")
    await send_online_devices_status()
    for ip in IP_NAME_MAPPING:
        await send_offline_devices_status(ip)

    # Stop all the task and start a new one
    asyncio.create_task(check_and_send_devices_status())
    await get_bot_status()

# Run the client and the check_and_send_devices_status task
async def main():
    await client.start()

    # Get and send initial status of all devices
    await send_online_devices_status()
    for ip in IP_NAME_MAPPING:
        await send_offline_devices_status(ip)

    # Perform a bot status check on the first run
    await get_bot_status()

    asyncio.create_task(check_and_send_devices_status())  # Start the status checking task
    await client.run_until_disconnected()


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
