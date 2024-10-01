from telegram import Update
from telegram.ext import ContextTypes
from config import ADMIN_CHAT_ID  # Import admin chat ID

command_states = {
    'speedtest': True,
    'ping': True,
    'music': True,
    'reboot': True
}

async def enable_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != ADMIN_CHAT_ID:  # Check user ID instead
        await context.bot.send_message(chat_id=update.effective_chat.id, text="You don't have permission to use this command.")
        return

    if len(context.args) != 1:
        await context.bot.send_message(chat_id=update.effective_chat.id, text='Usage: /enable <command>')
        return

    command = context.args[0].strip('!')

    if command in command_states:
        command_states[command] = True
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"{command} has been enabled.")
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Command '{command}' not found.")

async def disable_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != ADMIN_CHAT_ID:  # Check user ID instead
        await context.bot.send_message(chat_id=update.effective_chat.id, text="You don't have permission to use this command.")
        return

    if len(context.args) != 1:
        await context.bot.send_message(chat_id=update.effective_chat.id, text='Usage: /disable <command>')
        return

    command = context.args[0].strip('!')

    if command in command_states:
        command_states[command] = False
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"{command} has been disabled.")
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Command '{command}' not found.")
