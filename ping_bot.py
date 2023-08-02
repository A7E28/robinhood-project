import logging
from telethon import TelegramClient, events, functions, types
import asyncio
import subprocess
from datetime import datetime, timedelta

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

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Print logs to the console
        logging.FileHandler('status_bot.log')  # Save logs to a file
    ]
)
logger = logging.getLogger(__name__)

# Dictionary to store the online status of devices
online_status = {}

# Dictionary to store the offline status of devices
offline_status = {}

# Dictionary to store the offline data (offline time and duration) of devices
offline_data = {ip: {'events': [], 'durations': []} for ip in IP_NAME_MAPPING}

async def check_status(ip):
    try:
        result = await asyncio.to_thread(subprocess.run, ['ping', '-n', '1', '-w', '2000', ip], capture_output=True)
        response = result.stdout.decode()
        if 'Reply from' in response:
            response_time = int(response.split("time=")[1].split("ms")[0])
            logger.info(f"Response from {ip}: {response_time} ms")
            return response_time
        else:
            logger.info(f"No response from {ip}")
            return None
    except Exception as e:
        logger.error(f"An error occurred while checking status for {ip}: {e}")
        return None

async def send_online_status():
    online_devices = []
    
    for ip, name in IP_NAME_MAPPING.items():
        response_time = await check_status(ip)
        
        if response_time is not None:
            online_devices.append(f"{name} ({ip}) - Response Time: {response_time} ms")
            online_status[ip] = response_time
            # Remove from offline_status if previously offline
            offline_status.pop(ip, None)
    
    if online_devices:
        online_message = "Online Devices:\n\n" + "\n".join(online_devices)
        await client.send_message(CHAT_ID, online_message)

async def send_offline_status(ip):
    offline_devices = []
    name = IP_NAME_MAPPING.get(ip, "Unknown Device")
    
    response_time = await check_status(ip)
    
    if response_time is None:
        if ip not in offline_status:
            # Device was previously online, set offline time
            offline_data[ip]['events'].append(datetime.now())
            logger.info(f"{name} ({ip}) is offline now.")
            
        offline_devices.append(f"{name} ({ip})")
        offline_status[ip] = True
        # Remove from online_status if previously online
        online_status.pop(ip, None)

    if offline_devices:
        offline_message = "Offline Devices:\n\n" + "\n".join(offline_devices)
        await client.send_message(CHAT_ID, offline_message)

async def send_offline_data():
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

async def check_and_send_status():
    while True:
        for ip, name in IP_NAME_MAPPING.items():
            if ip in online_status:
                # Device is already marked as online, check if it is still online
                response_time = await check_status(ip)
                if response_time is None:
                    logger.info(f"{name} ({ip}) is offline now.")
                    # Device is offline now, send offline status message
                    await send_offline_status(ip)
            else:
                # Device is not marked as online, check if it is online now
                response_time = await check_status(ip)
                if response_time is not None:
                    logger.info(f"{name} ({ip}) is online now. Response Time: {response_time} ms")
                    # Device is online now, send online status message
                    online_status[ip] = response_time
                    online_message = f"{name} ({ip}) - Response Time: {response_time} ms"
                    await client.send_message(CHAT_ID, online_message)

                    # Check if the device was previously offline
                    if ip in offline_status:
                        await client.send_message(CHAT_ID, f"{name} ({ip}) is online now.")
                        logger.info(f"{name} ({ip}) is online now.")
                        # Remove from offline_status since it's online now
                        offline_status.pop(ip, None)
        
        await asyncio.sleep(5)  # Wait for 5 seconds before checking again

@client.on(events.NewMessage(pattern='/status'))
async def get_status(event):
    # Get the current online status of all devices
    await send_online_status()

    # Get the offline status of devices and send them as well
    offline_devices = [f"{name} ({ip})" for ip, name in IP_NAME_MAPPING.items() if ip in offline_status]
    if offline_devices:
        offline_message = "Offline Devices:\n\n" + "\n".join(offline_devices)
        await client.send_message(CHAT_ID, offline_message)

@client.on(events.NewMessage(pattern='/time'))
async def get_offline_data(event):
    await send_offline_data()

# Command to send the log file as a text file
@client.on(events.NewMessage(pattern='/log'))
async def send_log(event):
    try:
        with open('status_bot.log', 'rb') as file:
            await client.send_file(event.chat_id, file, caption='Status Bot Log')
    except Exception as e:
        await client.send_message(event.chat_id, f"An error occurred while sending the log file: {e}")

# Run the client and the check_and_send_status task
async def main():
    await client.start()

    logger.info("Status bot started.")

    # Get and send initial status of all devices
    await send_online_status()
    for ip in IP_NAME_MAPPING:
        await send_offline_status(ip)

    asyncio.create_task(check_and_send_status())  # Start the status checking task
    await client.run_until_disconnected()

loop = asyncio.get_event_loop()
loop.run_until_complete(main())

