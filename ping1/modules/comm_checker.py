from telegram import Update
from telegram.ext import ContextTypes
from ping1.modules.helper.restricted import boss

command_states = {
    'speedtest': True,
    'ping': True,
    'music': True,
    'reboot': True
}

@boss
async def enable_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) != 1:
        await context.bot.send_message(chat_id=update.effective_chat.id, text='Usage: /enable <command>')
        return

    command = context.args[0].strip('!')

    if command in command_states:
        command_states[command] = True
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"{command} has been enabled.")
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Command '{command}' not found.")

@boss
async def disable_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) != 1:
        await context.bot.send_message(chat_id=update.effective_chat.id, text='Usage: /disable <command>')
        return

    command = context.args[0].strip('!')

    if command in command_states:
        command_states[command] = False
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"{command} has been disabled.")
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Command '{command}' not found.")
