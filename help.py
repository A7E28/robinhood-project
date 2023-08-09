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
            "/all_status - this will check and send status of all the device from device.txt"
            "/status_device(device name or ip) - this will provide the mentioned device in the command"
	    "/subnet_calculator - this is a subetmask and cidr convert calculator"
        )
        await event.respond(help_text)
        raise events.StopPropagation
