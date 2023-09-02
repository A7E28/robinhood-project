import time
import telebot
from credentials import BOT_TOKEN

# Initialize the TeleBot instance with the API token
bot = telebot.TeleBot(BOT_TOKEN)

# Initialize bot start time
start_time = time.time()

# Register the help feature with the bot
import help
help.register_help_feature(bot)

# Register the start feature with the bot
import start
start.register_start_feature(bot)

# Register the bot_status feature with the bot and pass start_time
import bot_status
bot_status.register_bot_status_feature(bot, start_time)

# Register the time feature with the bot
import time_feature
time_feature.register_time_feature(bot)

# Register the ping feature with the bot
from ping import register_ping_feature
register_ping_feature(bot)

# Polling loop to keep the bot running
bot.polling(none_stop=True)
