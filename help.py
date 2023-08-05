import telebot

def register_help_feature(bot):
    @bot.message_handler(commands=['help'])
    def help(message):
        help_text = (
            "List of available commands:\n"
            "/start - Start the bot\n"
            "/help - Display this help message\n"
            "/time - Show current date and time"
        )
        bot.reply_to(message, help_text)
