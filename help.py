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
            "/all_status - Check and send status of all devices from device.json\n"
            "/status_device(device name or ip) - Provide the status of the mentioned device\n"
            "/subnet_calculator - Subnet mask and CIDR value converter\n"
            "/setlocation (your desired location) - Set your location for weather information\n"
            "/weather - Get weather information for your set location\n"
            "/add_device (name), (IP) - Add a new device to the list\n"
            "/remove_device (name or IP) - Remove a device from the list\n"
            "/device_list - List all devices in the device.json"
        )
        await event.respond(help_text)
        raise events.StopPropagation
