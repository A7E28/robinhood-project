from telethon import TelegramClient, events
import asyncio
import schedule
import subprocess

# Telegram API credentials
API_ID = app_id
API_HASH = 'api_has'
BOT_TOKEN = 'bot_token'

# Chat ID where the updates will be sent
CHAT_ID = chat_id

# IP addresses and their corresponding names
IP_NAME_MAPPING = {
    "8.8.8.8": "Google DNS",
    "192.168.1.1": "Router",
    "192.168.1.104": "Mobile",
}

# Initialize the Telegram client
client = TelegramClient('status_bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)


async def check_status(ip):
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


async def send_status():
    online_devices = []
    offline_devices = []
    
    for ip, name in IP_NAME_MAPPING.items():
        response_time = await check_status(ip)
        
        if response_time is not None:
            online_devices.append(f"{name} ({ip}) - Response Time: {response_time} ms")
        else:
            offline_devices.append(f"{name} ({ip})")
    
    if online_devices:
        online_message = "Online Devices:\n\n" + "\n".join(online_devices)
        await client.send_message(CHAT_ID, online_message)
    
    if offline_devices:
        offline_message = "Offline Devices:\n\n" + "\n".join(offline_devices)
        await client.send_message(CHAT_ID, offline_message)


@client.on(events.NewMessage(pattern='/status'))
async def get_status(event):
    await send_status()


async def run_schedule():
    while True:
        schedule.run_pending()
        await asyncio.sleep(1)


# Schedule the status update every 5 seconds
schedule.every(5).seconds.do(lambda: asyncio.create_task(send_status()))

# Run the client
async def main():
    await client.start()
    await client.run_until_disconnected()


loop = asyncio.get_event_loop()
loop.create_task(main())
loop.create_task(run_schedule())
loop.run_forever()
