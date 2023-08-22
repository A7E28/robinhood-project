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
from ping3 import ping, verbose_ping
from credentials import API_ID, API_HASH, BOT_TOKEN, CHAT_ID

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
            new_ip_name_mapping = load_device_info()

            # Remove devices that are no longer in the new mapping
            for ip in IP_NAME_MAPPING.keys():
                if ip not in new_ip_name_mapping:
                    if ip in online_status:
                        offline_status[ip] = True
                    offline_data.pop(ip, None)
                    online_status.pop(ip, None)

            # Update the IP_NAME_MAPPING with the new mapping
            IP_NAME_MAPPING.clear()
            IP_NAME_MAPPING.update(new_ip_name_mapping)

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
        tasks = []

        # Dictionary to store updated online/offline status for devices
        updated_status = {}

        for ip, name in IP_NAME_MAPPING.items():
            response_time = await ping_ip(ip)
            if ip in online_status:
                if response_time is None:
                    # Device is offline now, mark as offline
                    updated_status[ip] = False
            else:
                if response_time is not None:
                    # Device is online now, mark as online
                    updated_status[ip] = True

        # Update the online/offline status for devices
        for ip, is_online in updated_status.items():
            if is_online:
                online_status[ip] = response_time
            else:
                offline_status[ip] = True
                # Remove from online_status since it's offline now
                online_status.pop(ip, None)
                tasks.append(send_offline_devices_status(ip))

        if tasks:
            await asyncio.gather(*tasks)

        await asyncio.sleep(30)  # Wait for 30 seconds before checking again



def register_monitor(client):

    @client.on(events.NewMessage(pattern='/offline_log'))
    async def get_offline_data(event):
        """
        Handler for the /log command to get and send the offline data of devices.
        """
        await send_offline_devices_data()


    @client.on(events.NewMessage(pattern='/report_sheet'))
    async def get_report_sheet(event):
        """
        Handler for the /report_sheet command to generate and send the Excel report sheet.
        """
        await generate_report_sheet()



    # Run the client and the check_and_send_devices_status task
    async def main():
        await client.start()

        # Get and send initial status of all devices
        await send_online_devices_status()
        for ip in IP_NAME_MAPPING:
            await send_offline_devices_status(ip)

        asyncio.create_task(check_and_send_devices_status())  # Start the status checking task
        await client.run_until_disconnected()


    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())