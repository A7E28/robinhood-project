#help.py
from telethon import events

def register_help_feature(client):
    @client.on(events.NewMessage(pattern='/help'))
    async def help(event):
        help_text = (
            "List of available commands:\n"
            "/start - Start the bot\n"
            "/help - Display this help message\n"
            "/time - Show current date and time\n"
            "/bot_status - Show the information of server\n"
            "/subnet_calculator - this is a subetmask and cidr convert calculator\n"
            "/setlocation (your desired location) - set your location to get wather information on /weather command\n"
            "/weather - for weather information of your given location\n"
            "/ip_info - for getting information of a ip or domain\n"
            "/mac_info - for getting mac/ vendor information\n"
            "/ping - for ping a ip or domain, -t for ping count\n"
        )
        await event.respond(help_text)
        raise events.StopPropagation
