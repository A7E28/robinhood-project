from telegram import Update
from telegram.ext import ContextTypes

async def bot_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        await context.bot.send_message(chat_id=update.effective_chat.id, text='Hello! I am your bot.')
    except Exception as e:
        print(f"Error in bot_start: {e}")
