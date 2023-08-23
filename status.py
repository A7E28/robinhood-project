from telethon import TelegramClient, events
import asyncio
from queue import Queue
import subprocess
from datetime import datetime, timedelta
import pandas as pd
import xlsxwriter
import psutil
import json
from credentials import API_ID, API_HASH, BOT_TOKEN, CHAT_ID

# Initialize the Telegram client
client = TelegramClient('status_bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# Read device information from device.json
with open('device.json', 'r') as json_file:
    device_data = json.load(json_file)

# Populate IP_NAME_MAPPING from device data
IP_NAME_MAPPING = {device['ip']: device['name'] for device in device_data['devices']}


# Dictionary to store the online status of devices
online_status = {}

# Dictionary to store the offline status of devices
offline_status = {}

# Dictionary to store the offline data (offline time and duration) of devices
offline_data = {ip: {'events': [], 'durations': []} for ip in IP_NAME_MAPPING}

# Create locks for dictionaries
online_status_lock = asyncio.Lock()
offline_status_lock = asyncio.Lock()
offline_data_lock = asyncio.Lock()


# Create a queue to hold pending device additions and removals
device_queue = Queue()

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
    while True:
        async with online_status_lock, offline_status_lock, offline_data_lock:
            # Your code to check status and update dictionaries
            for ip in list(IP_NAME_MAPPING.keys()):
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
                        name = IP_NAME_MAPPING[ip]
                        online_message = f"{name} ({ip}) - Response Time: {response_time} ms"
                        await client.send_message(CHAT_ID, online_message)

                        # Check if the device was previously offline
                        if ip in offline_status:
                            await client.send_message(CHAT_ID, f"{name} ({ip}) is online now.")
                            # Remove from offline_status since it's online now
                            offline_status.pop(ip, None)
        
        await asyncio.sleep(5)

# add_device function
async def add_device(name, ip):
    async with offline_data_lock:
        with open('device.json', 'r') as json_file:
            device_data = json.load(json_file)
            
        new_device = {"name": name, "ip": ip}
        device_data['devices'].append(new_device)
        
        with open('device.json', 'w') as json_file:
            json.dump(device_data, json_file, indent=4)

        IP_NAME_MAPPING[ip] = name
        online_status[ip] = None  # Initialize online status
        offline_data[ip] = {'events': [], 'durations': []}

#remove_device function
async def remove_device(name):
    async with offline_data_lock:
        with open('device.json', 'r') as json_file:
            device_data = json.load(json_file)
            
        device_to_remove = None
        for device in device_data['devices']:
            if device['name'] == name:
                device_to_remove = device
                break
                
        if device_to_remove:
            ip = device_to_remove['ip']
            device_data['devices'].remove(device_to_remove)
            
            with open('device.json', 'w') as json_file:
                json.dump(device_data, json_file, indent=4)
                
            IP_NAME_MAPPING.pop(ip, None)
            online_status.pop(ip, None)
            offline_data.pop(ip, None)



# Check the status of all devices available in device.json
async def check_all_devices_status():
    status_message = "Device Status:\n\n"
    
    for ip, name in IP_NAME_MAPPING.items():
        response_time = await ping_ip(ip)
        status = "Online" if response_time is not None else "Offline"
        status_message += f"{name} ({ip}): {status}\n"
    
    await client.send_message(CHAT_ID, status_message)

# Check the status of a specific device by name
async def check_device_status(name):
    ip = next((ip for ip, device_name in IP_NAME_MAPPING.items() if device_name == name), None)
    
    if ip:
        response_time = await ping_ip(ip)
        status = "Online" if response_time is not None else "Offline"
        status_message = f"{name} ({ip}): {status}"
        await client.send_message(CHAT_ID, status_message)
    else:
        await client.send_message(CHAT_ID, f"Device '{name}' not found.")

# Function to list all available devices from device.json
async def list_available_devices():
    available_devices = "\n".join([f"{name} ({ip})" for ip, name in IP_NAME_MAPPING.items()])
    if available_devices:
        devices_message = f"Available Devices:\n\n{available_devices}"
        await client.send_message(CHAT_ID, devices_message)
    else:
        await client.send_message(CHAT_ID, "No devices available.")


# In your main event loop, periodically check the queue and process pending device changes
async def check_device_queue():
    while True:
        if not device_queue.empty():
            action, *params = device_queue.get()
            if action == 'add':
                name, ip = params
                await add_device(name, ip)
                print(f"Device '{name}' with IP '{ip}' added.")
            elif action == 'remove':
                name = params[0]
                await remove_device(name)
                print(f"Device '{name}' removed.")
        await asyncio.sleep(5)  # Adjust the interval as needed

def register_status(client):

    # Event handler for /list_device command
    @client.on(events.NewMessage(pattern='/list_device'))
    async def list_device_command(event):
        await list_available_devices()

    @client.on(events.NewMessage(pattern='/add_device'))
    async def add_device_command(event):
        args = event.raw_text.split()[1:]
        if len(args) != 2:
            await event.reply("Usage: /add_device <name> <ip>")
        else:
            name, ip = args
            device_queue.put(('add', name, ip))  # Add the device info to the queue
            await add_device(name, ip)  # Immediately add the device
            await event.reply(f"Device '{name}' with IP '{ip}' has been added.")


    @client.on(events.NewMessage(pattern='/remove_device'))
    async def remove_device_command(event):
        args = event.raw_text.split()[1:]
        if len(args) != 1:
            await event.reply("Usage: /remove_device <name>")
        else:
            name = args[0]
            device_queue.put(('remove', name))  # Add the device removal info to the queue
            await remove_device(name)  # Immediately remove the device
            await event.reply(f"Device '{name}' has been removed.")


    # Event handler for /all_status command
    @client.on(events.NewMessage(pattern='/all_status'))
    async def all_status_command(event):
        await check_all_devices_status()

    # Event handler for /device_status command
    @client.on(events.NewMessage(pattern='/device_status'))
    async def device_status_command(event):
        args = event.raw_text.split()[1:]
        if len(args) != 1:
            await event.reply("Usage: /device_status <name>")
        else:
            name = args[0]
            await check_device_status(name)

    @client.on(events.NewMessage(pattern='/offline_log'))
    async def get_offline_data(event):
        """
        Handler for the /offline_log command to get and send the offline data of devices.
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
        
        # Start the check_device_queue task
        asyncio.create_task(check_device_queue())

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
