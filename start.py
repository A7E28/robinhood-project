import telebot

def register_start_feature(bot):
    @bot.message_handler(commands=['start'])
    def start(message):
        bot.reply_to(message, "Hello! I am your Telegram bot!")
