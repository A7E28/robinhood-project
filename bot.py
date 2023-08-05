# bot.py

import time
from telethon import TelegramClient, events
from credentials import API_ID, API_HASH, BOT_TOKEN, CHAT_ID
import subprocess
import help
import start
from bot_status import register_bot_status_feature

# Initialize the Telegram client
client = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# Initialize bot start time
start_time = time.time()

# Register the help feature with the client
help.register_help_feature(client)

# Register the start feature with the client
start.register_start_feature(client)

# Register the bot_status feature with the client and pass start_time
register_bot_status_feature(client, start_time)

# Run the client
client.run_until_disconnected()
