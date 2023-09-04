from telethon import TelegramClient, events
import asyncio
import subprocess
from ping3 import ping
import json
import os
import time
import pytz
from datetime import datetime, timedelta
import pandas as pd
import xlsxwriter
import cachetools
import schedule

# Initialize the chat IDs from a JSON file
initialized_chats_file = "initialized_chats.json"
initialized_chats = set()  # Use a set to store chat-specific data

if os.path.exists(initialized_chats_file):
    with open(initialized_chats_file, "r") as file:
        initialized_chats = set(json.load(file))
        print(f"Chat IDs {initialized_chats} loaded from JSON file.")

# Load initial device information from device.json
def load_device_info():
    with open('device.json', 'r') as json_file:
        data = json.load(json_file)
    return {device['ip']: device['name'] for device in data['devices']}

# Initial loading of device information
IP_NAME_MAPPING = load_device_info()

# Create dictionaries to store chat-specific data
chat_online_status = {}  # For online status
chat_offline_status = {}  # For offline status
chat_offline_data = {}  # For offline data

MIN_PING_TIMEOUT = 1  # Minimum timeout in seconds
MAX_PING_TIMEOUT = 5  # Maximum timeout in seconds

# Initialize a cache with a maximum size
cache = cachetools.LRUCache(maxsize=100)  # You can adjust the maxsize as needed

async def ping_ip(ip):
    """
    Pings an IP address and returns the response time in milliseconds if successful, else returns None.
    """
    try:
        # Check if the result is in the cache
        if ip in cache:
            return cache[ip]

        response_time = ping(ip, timeout=5)  # Sending an ICMP ping request with a timeout of 2 seconds

        if response_time is not None:
            # Set a dynamic timeout based on response time
            dynamic_timeout = max(MIN_PING_TIMEOUT, min(MAX_PING_TIMEOUT, response_time / 1000))

            # Sending another ping with the dynamic timeout
            response_time = ping(ip, timeout=dynamic_timeout)

            if response_time is not None:
                # Cache the result for future use
                cache[ip] = int(response_time * 1000)  # Convert seconds to milliseconds
                return cache[ip]

        return None
    except Exception:
        return None


# send_online_devices_status function
async def send_online_devices_status(event):
    chat_id = event.chat_id
    online_devices = []

    chat_online_status_data = chat_online_status.get(chat_id, {})
    
    # code to use chat-specific data
    for ip, name in IP_NAME_MAPPING.items():
        response_time = await ping_ip(ip)
        if response_time is not None:
            online_devices.append(f"{name} ({ip}) - Response Time: {response_time} ms")
            chat_online_status_data[ip] = response_time
            # Remove from offline_status if previously offline
            chat_offline_status.get(chat_id, {}).pop(ip, None)

    # Update chat-specific data
    chat_online_status[chat_id] = chat_online_status_data
    
    if online_devices:
        online_message = "Online Devices:\n\n" + "\n".join(online_devices)
        await event.respond(online_message)

# send_offline_devices_status function
async def send_offline_devices_status(event, ip):
    chat_id = event.chat_id
    offline_devices = []
    name = IP_NAME_MAPPING.get(ip, "Unknown Device")

    response_time = await ping_ip(ip)

    if response_time is None:
        if ip not in chat_offline_status.get(chat_id, {}):
            # Device was previously online, set offline time
            dhaka_time = datetime.now(pytz.timezone('Asia/Dhaka'))
            chat_offline_data.setdefault(chat_id, {}).setdefault(ip, {}).setdefault('events', []).append(dhaka_time)

        offline_devices.append(f"{name} ({ip})")
        chat_offline_status.setdefault(chat_id, {})[ip] = True
        # Remove from online_status if previously online
        chat_online_status.get(chat_id, {}).pop(ip, None)

    if offline_devices:
        offline_message = "Offline Devices:\n\n" + "\n".join(offline_devices)
        await event.respond(offline_message)

# send_offline_devices_data function
async def send_offline_devices_data(event):
    chat_id = event.chat_id
    offline_data_message = "Offline Device Data:\n\n"
    chat_offline_data_for_chat = chat_offline_data.get(chat_id, {})

    for ip, data in chat_offline_data_for_chat.items():
        name = IP_NAME_MAPPING.get(ip, "Unknown Device")
        offline_events = data.get('events', [])
        offline_durations = data.get('durations', [])

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

# handle_start_command function
async def handle_start_command(event):
    chat_id = event.chat_id
    print(f"Detected chat ID: {chat_id}")

    if chat_id in initialized_chats:
        print(f"Chat ID {chat_id} is already initialized.")
        await event.respond("Monitoring is already running.")
    else:
        print(f"Chat ID {chat_id} is being initialized.")
        # Save the chat ID to the set and JSON file
        initialized_chats.add(chat_id)
        with open(initialized_chats_file, "w") as file:
            json.dump(list(initialized_chats), file)
            print(f" chat id is saved")

        # Continue with the initialization logic
        await send_online_devices_status(event)
        for ip in IP_NAME_MAPPING:
            await send_offline_devices_status(event, ip)
        await check_and_send_devices_status(event)  # Moved this line here
        

# Modify generate_report_sheet function
async def generate_report_sheet(event):
    chat_id = event.chat_id
    offline_devices_data = []
    columns = ['Device', 'IP', 'Offline Time', 'Online Time', 'Offline Duration']

    chat_offline_data_for_chat = chat_offline_data.get(chat_id, {})

    for ip, data in chat_offline_data_for_chat.items():
        name = IP_NAME_MAPPING.get(ip, "Unknown Device")
        offline_events = data.get('events', [])
        offline_durations = data.get('durations', [])

        for i, offline_time in enumerate(offline_events):
            dhaka_time = datetime.now(pytz.timezone('Asia/Dhaka'))
            duration = dhaka_time - offline_time
            online_time = offline_time + duration
            offline_durations.append(duration)

            offline_devices_data.append(
                [name, ip, offline_time.strftime('%H:%M'), online_time.strftime('%H:%M'), str(duration).split('.')[0]])

    df = pd.DataFrame(offline_devices_data, columns=columns)

    # Create a new Excel workbook using xlsxwriter
    file_name = f"offline_report.xlsx"
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
        status_message += f"{name} ({ip}): {status}: {response_time} ms\n"
    
    await event.respond(status_message)

# Check the status of a specific device by name
async def check_device_status(event, name):
    chat_id = event.chat_id
    ip = next((ip for ip, device_name in IP_NAME_MAPPING.items() if device_name == name), None)
    
    if ip:
        response_time = await ping_ip(ip)
        status = "Online" if response_time is not None else "Offline"
        status_message = f"{name} ({ip}): {status}: {response_time} ms"
        await event.respond(status_message)
    else:
        await event.respond(f"Device '{name}' not found.")

# Function to list all available devices from device.json
async def list_available_devices(event):
    chat_id = event.chat_id
    available_devices = "\n".join([f"{name} ({ip})" for ip, name in IP_NAME_MAPPING.items()])
    if available_devices:
        devices_message = f"Available Devices:\n\n{available_devices}"
        await event.respond(devices_message)
    else:
        await event.respond("No devices available.")        

async def check_and_send_devices_status(event):
    chat_id = event.chat_id
    print(f"check_and_send_devices_status task started for chat_id: {chat_id}")  # Add this line

    # Create a list of tasks to ping all IP addresses concurrently
    ping_tasks = [ping_ip(ip) for ip in IP_NAME_MAPPING]

    # Gather the results concurrently
    ping_results = await asyncio.gather(*ping_tasks)

    for ip, name in IP_NAME_MAPPING.items():
        response_time = ping_results.pop(0)  # Get the result corresponding to this IP

        if ip in chat_online_status.get(chat_id, {}):
            # Device is already marked as online, check if it is still online
            if response_time is None:
                # Device is offline now, send offline status message
                await send_offline_devices_status(event, ip)
        else:
            # Device is not marked as online, check if it is online now
            if response_time is not None:
                # Device is online now, send online status message
                online_status_data = chat_online_status.setdefault(chat_id, {})
                online_status_data[ip] = response_time
                await send_online_status_message(event, name, ip, response_time)

                # Check if the device was previously offline
                if ip in chat_offline_status.get(chat_id, {}):
                    await send_device_online_notification(event, name, ip)
                    # Remove from offline_status since it's online now
                    chat_offline_status.get(chat_id, {}).pop(ip, None)

    await asyncio.sleep(5)  # Wait for 5 seconds before checking again


async def send_online_status_message(event, name, ip, response_time):
    online_message = f"{name} ({ip}) - Response Time: {response_time} ms"
    await event.respond(online_message)

async def send_device_online_notification(event, name, ip):
    online_notification = f"{name} ({ip}) is online now."
    await event.respond(online_notification)

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

    # event handler for /start
    @client.on(events.NewMessage(pattern='/start'))
    async def start(event):
        chat_id = event.chat_id
        await event.respond("Hello! I am your Telegram bot. Device monitoring has been started.")
        await handle_start_command(event)
        
        # Schedule the all_status command to run daily at 10 am
        schedule.every().day.at("10:00").do(send_all_status_command, event)

        raise events.StopPropagation

    # Function to send the /all_status command
    async def send_all_status_command(event):
        await check_all_devices_status(event)

    # Run the client
    async def register_status(client):
        await client.start()
        
        # Run the scheduled jobs in the background
        while True:
            schedule.run_pending()
            await asyncio.sleep(1)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(register_status(client))
