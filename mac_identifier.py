import requests
from telethon import events
import json

# Define a function to check if a user is in the specified group
def is_user_in_group(user_id, group_name):
    user_groups = load_user_groups()  # Load user group data every time
    if group_name in user_groups:
        return user_id in user_groups[group_name]
    return False

# Load user group data from user_id.json file
def load_user_groups():
    try:
        with open("user_id.json", "r") as file:
            data = json.load(file)
            if isinstance(data, dict):
                return data
    except FileNotFoundError:
        return {}
        
# Define a function to handle the /mac_info command
async def mac_info_command(event):
    user_id = event.sender_id
    # Check if the user is in any group listed in user_id.json
    user_groups = load_user_groups()
    if any(is_user_in_group(user_id, group_name) for group_name in user_groups):
        
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
    else:
        await event.respond("You do not have access to this command.")    
                        

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
