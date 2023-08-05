from telethon import TelegramClient, events
from telethon import events
from credentials import API_ID, API_HASH, BOT_TOKEN, CHAT_ID
import subprocess
import time_feature
import help
import start
import status 

# Initialize the Telegram client
client = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# Register the time feature with the client
time_feature.register_time_feature(client)

# Register the help feature with the client
help.register_help_feature(client)

# Register the start feature with the client
start.register_start_feature(client)

# Register the status feature with the client
status.register_status_feature(client)

# Run the client
client.run_until_disconnected()
