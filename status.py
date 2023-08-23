from telethon import TelegramClient, events
import asyncio
import subprocess
from datetime import datetime, timedelta
import pandas as pd
import xlsxwriter
import psutil
import json
import os
import time
import pytz
from ping3 import ping, verbose_ping
from credentials import API_ID, API_HASH, BOT_TOKEN

# Initialize the Telegram client
client = TelegramClient('status_bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# Load initial device information from device.json
def load_device_info():
    with open('device.json', 'r') as json_file:
        data = json.load(json_file)
    return {device['ip']: device['name'] for device in data['devices']}

def watch_device_json_changes():
    previous_mtime = os.path.getmtime('device.json')
    
    while True:
        current_mtime = os.path.getmtime('device.json')
        
        if current_mtime != previous_mtime:
            print("device.json has changed. Reloading device information.")
            IP_NAME_MAPPING = load_device_info()
            previous_mtime = current_mtime
        
        time.sleep(5)  # Wait for 5 seconds before checking again

# Initial loading of device information
IP_NAME_MAPPING = load_device_info()

# Start a separate thread to watch for device.json changes
import threading
watch_thread = threading.Thread(target=watch_device_json_changes)
watch_thread.start()


# Dictionary to store the online status of devices
online_status = {}

# Dictionary to store the offline status of devices
offline_status = {}

# Dictionary to store the offline data (offline time and duration) of devices
offline_data = {ip: {'events': [], 'durations': []} for ip in IP_NAME_MAPPING}

# Global variable to store the start time of the bot
start_time = None

MIN_PING_TIMEOUT = 1  # Minimum timeout in seconds
MAX_PING_TIMEOUT = 5  # Maximum timeout in seconds

async def ping_ip(ip):
    """
    Pings an IP address and returns the response time in milliseconds if successful, else returns None.
    """
    try:
        response_time = ping(ip, timeout=2)  # Sending an ICMP ping request with a timeout of 2 seconds

        if response_time is not None:
            # Set a dynamic timeout based on response time
            dynamic_timeout = max(MIN_PING_TIMEOUT, min(MAX_PING_TIMEOUT, response_time / 1000))

            # Sending another ping with the dynamic timeout
            response_time = ping(ip, timeout=dynamic_timeout)

            if response_time is not None:
                return int(response_time * 1000)  # Convert seconds to milliseconds

        return None
    except Exception:
        return None

async def send_online_devices_status(event):
        
    """
    Checks the online status of devices and sends the list of online devices to the chat.
    """
    chat_id = event.chat_id
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
        await event.respond(online_message)


async def send_offline_devices_status(event, ip):
    """
    Checks the offline status of a specific device and sends the offline message to the chat.
    """
    chat_id = event.chat_id
    offline_devices = []
    name = IP_NAME_MAPPING.get(ip, "Unknown Device")

    response_time = await ping_ip(ip)

    if response_time is None:
        if ip not in offline_status:
            # Device was previously online, set offline time
            dhaka_time = datetime.now(pytz.timezone('Asia/Dhaka'))
            offline_data[ip]['events'].append(dhaka_time)

        offline_devices.append(f"{name} ({ip})")
        offline_status[ip] = True
        # Remove from online_status if previously online
        online_status.pop(ip, None)

    if offline_devices:
        offline_message = "Offline Devices:\n\n" + "\n".join(offline_devices)
        await event.respond(offline_message)


async def send_offline_devices_data(event):
    """
    Sends the offline data (offline time and duration) of devices to the chat.
    """
    chat_id = event.chat_id
    offline_data_message = "Offline Device Data:\n\n"
    for ip, data in offline_data.items():
        name = IP_NAME_MAPPING.get(ip, "Unknown Device")
        offline_events = data['events']
        offline_durations = data['durations']

        for i, offline_time in enumerate(offline_events):
            dhaka_time = datetime.now(pytz.timezone('Asia/Dhaka'))
            duration = dhaka_time - offline_time            
            online_time = offline_time + duration
            offline_durations.append(duration)
            offline_data_message += f"{name} ({ip})\n"
            offline_data_message += f"Offline Time: {offline_time.strftime('%H:%M')}\n"
            offline_data_message += f"Online Time: {online_time.strftime('%H:%M')}\n"
            offline_data_message += f"Offline Duration: {str(duration).split('.')[0]}\n\n"

    if offline_data_message != "Offline Device Data:\n\n":
        await event.respond(offline_data_message)


async def generate_report_sheet(event):
    """
    Generates an Excel report sheet containing the offline data (offline time and duration) of devices.
    """
    chat_id = event.chat_id
    offline_devices_data = []
    columns = ['Device', 'IP', 'Offline Time', 'Online Time', 'Offline Duration']

    for ip, data in offline_data.items():
        name = IP_NAME_MAPPING.get(ip, "Unknown Device")
        offline_events = data['events']
        offline_durations = data['durations']

        for i, offline_time in enumerate(offline_events):
            dhaka_time = datetime.now(pytz.timezone('Asia/Dhaka'))
            duration = dhaka_time - offline_time
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
    await event.respond(file=file_name)

# Check the status of all devices available in device.json
async def check_all_devices_status(event):
    chat_id = event.chat_id
    status_message = "Device Status:\n\n"
    
    for ip, name in IP_NAME_MAPPING.items():
        response_time = await ping_ip(ip)
        status = "Online" if response_time is not None else "Offline"
        status_message += f"{name} ({ip}): {status}\n"
    
    await client.send_message(chat_id, status_message)

# Check the status of a specific device by name
async def check_device_status(event, name):
    chat_id = event.chat_id
    ip = next((ip for ip, device_name in IP_NAME_MAPPING.items() if device_name == name), None)
    
    if ip:
        response_time = await ping_ip(ip)
        status = "Online" if response_time is not None else "Offline"
        status_message = f"{name} ({ip}): {status}"
        await client.send_message(chat_id, status_message)
    else:
        await client.send_message(chat_id, f"Device '{name}' not found.")

# Function to list all available devices from device.json
async def list_available_devices(event):
    chat_id = event.chat_id
    available_devices = "\n".join([f"{name} ({ip})" for ip, name in IP_NAME_MAPPING.items()])
    if available_devices:
        devices_message = f"Available Devices:\n\n{available_devices}"
        await client.send_message(chat_id, devices_message)
    else:
        await client.send_message(chat_id, "No devices available.")

async def check_and_send_devices_status(event):
    """
    Periodically checks the online status of devices and sends status messages to the chat.
    """
    chat_id = event.chat_id
    print(f"check_and_send_devices_status task started for chat_id: {chat_id}")  # Add this line
    while True:
        for ip, name in IP_NAME_MAPPING.items():
            if ip in online_status:
                # Device is already marked as online, check if it is still online
                response_time = await ping_ip(ip)
                if response_time is None:
                    # Device is offline now, send offline status message
                    await send_offline_devices_status(event, ip)
            else:
                # Device is not marked as online, check if it is online now
                response_time = await ping_ip(ip)
                if response_time is not None:
                    # Device is online now, send online status message
                    online_status[ip] = response_time
                    online_message = f"{name} ({ip}) - Response Time: {response_time} ms"
                    await event.respond(online_message)

                    # Check if the device was previously offline
                    if ip in offline_status:
                        await event.respond(f"{name} ({ip}) is online now.")
                        # Remove from offline_status since it's online now
                        offline_status.pop(ip, None)

        await asyncio.sleep(5)  # Wait for 5 seconds before checking again

def register_status(client):

    @client.on(events.NewMessage(pattern='/offline_log'))
    async def get_offline_data(event):
        """
        Handler for the /log command to get and send the offline data of devices.
        """
        await send_offline_devices_data(event)


    @client.on(events.NewMessage(pattern='/report_sheet'))
    async def get_report_sheet(event):
        """
        Handler for the /report_sheet command to generate and send the Excel report sheet.
        """
        await generate_report_sheet(event)

    # Event handler for /all_status command
    @client.on(events.NewMessage(pattern='/all_status'))
    async def all_status_command(event):
        await check_all_devices_status(event)

    # Event handler for /device_status command
    @client.on(events.NewMessage(pattern='/device_status'))
    async def device_status_command(event):
        args = event.raw_text.split()[1:]
        if len(args) != 1:
            await event.reply("Usage: /device_status <name>")
        else:
            name = args[0]
            await check_device_status(event, name)

    # Event handler for /list_device command
    @client.on(events.NewMessage(pattern='/list_device'))
    async def list_device_command(event):
        await list_available_devices(event)

    # Define a new function to handle the /start command
    async def handle_start_command(event):
        """
        Handler for the /start command to start the monitoring task.
        """
        # Get and send initial status of all devices
        await send_online_devices_status(event)
        for ip in IP_NAME_MAPPING:
            await send_offline_devices_status(event, ip)

        # Start the status checking task for the specific chat where /start was sent
        await check_and_send_devices_status(event)

    # Update the event handler for the /start command to call handle_start_command
    @client.on(events.NewMessage(pattern='/start'))
    async def start(event):
        await event.respond("Hello! I am your Telegram bot And device monitoring has been started")
        await handle_start_command(event)
        raise events.StopPropagation

    # Run the client
    async def main():
        await client.start()
        await client.run_until_disconnected()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())