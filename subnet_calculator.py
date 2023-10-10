# subnet_calculator.py

import ipaddress
from telethon import events, Button
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

# Function to calculate subnet information
def calculate_subnet_info(ip_address, subnet_mask):
    network = ipaddress.IPv4Network(f"{ip_address}/{subnet_mask}", strict=False)
    gateway = network.network_address + 1
    return {
        "Network Address": str(network.network_address),
        "Broadcast Address": str(network.broadcast_address),
        "Usable Host IP Range": f"{gateway} - {network.broadcast_address - 1}",
        "Gateway Address": str(gateway),
        "Total Hosts": network.num_addresses - 2,
    }

# Function to convert CIDR notation to subnet info
def convert_cidr_to_subnet(cidr):
    network = ipaddress.IPv4Network(cidr, strict=False)
    return str(network.network_address), str(network.netmask)

def convert_subnet_to_cidr(network_address, subnet_mask):
    subnet_mask_length = sum([bin(int(x)).count("1") for x in subnet_mask.split(".")])
    cidr = f"{network_address}/{subnet_mask_length}"
    return cidr

# Function to format subnet information
def format_subnet_info(subnet_info):
    return "\n".join([f"{key}: {value}" for key, value in subnet_info.items()])

# Function to format CIDR conversion
def format_cidr_conversion(network_address, subnet_mask):
    return f"Network Address: {network_address}\nSubnet Mask: {subnet_mask}"

# Define a dictionary to store user states
user_states = {}

def register_subnet_calculator_feature(client):
    @client.on(events.NewMessage(pattern='/subnet_calculator'))
    async def subnet_calculator(event):
        user_id = event.sender_id
        # Check if the user is in any group listed in user_id.json
        user_groups = load_user_groups()
        if any(is_user_in_group(user_id, group_name) for group_name in user_groups):
            buttons = [
                [Button.inline("Calculate Subnet", data="calculate")],
                [Button.inline("CIDR to Subnet", data="cidr2subnet")],
                [Button.inline("Subnet to CIDR", data="subnet2cidr")]
            ]
            
            await event.respond(
                "Choose an action:",
                buttons=buttons,  # Add buttons here
                reply_to=event.message.id
            )
        else:
            await event.respond("You do not have access to this command.")
        
    @client.on(events.CallbackQuery(pattern=b'calculate'))
    async def calculate_action(event):
        user_id = event.sender_id
        user_states[user_id] = "calculate"
        await event.edit("Enter IP address and subnet mask separated by space.\nExample: 192.168.1.10 24")

    @client.on(events.CallbackQuery(pattern=b'cidr2subnet'))
    async def cidr2subnet_action(event):
        user_id = event.sender_id
        user_states[user_id] = "cidr2subnet"
        await event.edit("Enter CIDR notation.\nExample: 192.168.2.0/23")

    @client.on(events.CallbackQuery(pattern=b'subnet2cidr'))
    async def subnet2cidr_action(event):
        user_id = event.sender_id
        user_states[user_id] = "subnet2cidr"
        await event.edit("Enter network address and subnet mask separated by space.\nExample: 10.0.0.0 255.255.255.0")

    @client.on(events.NewMessage)
    async def handle_input(event):
        user_id = event.sender_id
        if user_id in user_states:
            action = user_states[user_id]
            del user_states[user_id]

            input_params = event.raw_text.split()
            if action == "calculate":
                if len(input_params) == 2:
                    ip_address, subnet_mask = input_params
                    try:
                        subnet_info = calculate_subnet_info(ip_address, subnet_mask)
                        response_msg = format_subnet_info(subnet_info)
                    except ValueError:
                        response_msg = "Invalid input format."
                else:
                    response_msg = "Invalid input format. Usage: IP_ADDRESS SUBNET_MASK"

            elif action == "cidr2subnet":
                if len(input_params) == 1:
                    cidr = input_params[0]
                    try:
                        network_address, subnet_mask = convert_cidr_to_subnet(cidr)
                        response_msg = format_cidr_conversion(network_address, subnet_mask)
                    except ValueError:
                        response_msg = "Invalid CIDR notation."
                else:
                    response_msg = "Invalid input format. Usage: CIDR"

            elif action == "subnet2cidr":
                if len(input_params) == 2:
                    network_address, subnet_mask = input_params
                    try:
                        cidr = convert_subnet_to_cidr(network_address, subnet_mask)
                        response_msg = f"Converted CIDR: {cidr}"
                    except ValueError:
                        response_msg = "Invalid input format or subnet."
                else:
                    response_msg = "Invalid input format. Usage: NETWORK_ADDRESS SUBNET_MASK"

            else:
                response_msg = "Invalid action."

            await event.respond(response_msg)
