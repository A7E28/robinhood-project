# main.py

import time
from telethon import TelegramClient, events
from credentials import API_ID, API_HASH, BOT_TOKEN, CHAT_ID
import help
import start
import time_feature
import status
from bot_status import register_bot_status_feature
import subnet_calculator
import weather
import location

# Initialize the Telegram client
client = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# Register the time feature with the client
time_feature.register_time_feature(client)

# Initialize bot start time
start_time = time.time()

# Register the help feature with the client
help.register_help_feature(client)

# Register the start feature with the client
start.register_start_feature(client)

# Register the status feature with the client
status.register_status_feature(client)

# Register the bot_status feature with the client and pass start_time
register_bot_status_feature(client, start_time)

# Register the subnet_calculator feature with the client
subnet_calculator.register_subnet_calculator_feature(client)

# Register the location feature with the client
location.register_location_feature(client)

# Register the weather feature with the client
weather.register_weather_feature(client)

# Run the client
client.run_until_disconnected()
