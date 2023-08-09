#help.py
from telethon import events

def register_help_feature(client):
    @client.on(events.NewMessage(pattern='/help'))
    async def help(event):
        help_text = (
            "List of available commands:\n"
            "/start - Start the bot\n"
            "/help - Display this help message\n"
            "/time - Show current date and time"
            "/bot_status - Show the information of server"
	    "/subnet_calculator - this is a subetmask and cidr convert calculator"
        )
        await event.respond(help_text)
        raise events.StopPropagation
