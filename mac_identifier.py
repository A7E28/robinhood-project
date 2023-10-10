import requests
from telethon import events

# Define a function to handle the /mac_info command
async def mac_info_command(event):
    # Get the user's input (the MAC address)
    user_input = event.text.split(" ", 1)
    
    if len(user_input) != 2:
        await event.reply("Please provide a MAC address.")
        return
    
    mac_address = user_input[1].strip()
    
    try:
        # Use the macvendors.com API to retrieve information about the MAC address
        mac_info = get_mac_info(mac_address)
        
        if mac_info:
            info_message = format_mac_info(mac_info, mac_address)
            await event.reply(info_message)
        else:
            await event.reply(f"Unable to retrieve information for MAC address: {mac_address}")
    except Exception as e:
        await event.reply(f"An error occurred: {str(e)}")

# Function to retrieve information about a MAC address using an API
def get_mac_info(mac_address):
    url = f"https://api.macvendors.com/{mac_address}"
    response = requests.get(url)
    
    if response.status_code == 200:
        return response.text
    else:
        return None

# Function to format MAC address information
def format_mac_info(mac_info, mac_address):
    info_message = f"Information for MAC address: {mac_address}\n\n"
    info_message += f"Vendor: {mac_info}\n"
    return info_message

# Register the /mac_info command handler with the client
def register_mac_info_feature(client):
    @client.on(events.NewMessage(pattern='/mac_info'))
    async def mac_info_handler(event):
        await mac_info_command(event)
