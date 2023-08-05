import telebot
import datetime

def register_time_feature(bot):
    @bot.message_handler(commands=['time'])
    def show_time(message):
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        bot.reply_to(message, f"Current date and time: {current_time}")
