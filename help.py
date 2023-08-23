from telethon import events

def register_help_feature(client):
    @client.on(events.NewMessage(pattern='/help'))
    async def help(event):
        help_text = (
            "List of available commands:\n"
            "List of available commands:\n"
            "/start - Start the bot\n"
            "/help - Display this help message\n"
            "/time - Show current date and time\n"
            "/bot_status - Show the information of server\n"
            "/subnet_calculator - Subnet mask and CIDR value converter\n"
            "/setlocation (your desired location) - Set your location for weather information\n"
            "/weather - Get weather information for your set location\n"
            "/add_device <name> <ip> - Add a device to monitor\n"
            "/remove_device <name> - Remove a device from monitoring\n"
            "/list_device - List all available devices\n"
            "/offline_log - Get offline data of devices\n"
            "/report_sheet - Generate an Excel report sheet of offline data\n"
        )
        await event.respond(help_text)
        raise events.StopPropagation
