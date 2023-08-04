import ping3
from telethon import events

# Define a dictionary to store devices and their corresponding IP addresses
device_list = {}

def read_devices_from_file(filename):
    # Read devices and their IP addresses from the specified file
    try:
        with open(filename, 'r') as f:
            for line in f:
                device_name, device_ip = line.strip().split()
                device_list[device_name] = device_ip
    except FileNotFoundError:
        print(f"Error: {filename} not found.")
    except Exception as e:
        print(f"Error occurred while reading {filename}: {e}")

def ping_device(ip):
    # Function to ping the device and get the response time
    try:
        response_time = ping3.ping(ip, timeout=1)
        if response_time is not None:
            return response_time * 1000  # Convert to milliseconds
        else:
            return None  # Device is offline
    except Exception:
        return None  # An error occurred, assume the device is offline

def register_device_status_feature(client):
    @client.on(events.NewMessage(pattern='/status'))
    async def get_device_status(event):
        # Split the user's message by spaces
        message_parts = event.message.text.split()

        # Check if the command has the correct format
        if len(message_parts) != 1:
            # The command has arguments, so it should be in the format /status <device_name>
            if len(message_parts) == 2:
                device_name = message_parts[1]
                # Check if the device name exists in the device_list
                if device_name in device_list:
                    device_ip = device_list[device_name]
                    response_time = ping_device(device_ip)
                    if response_time is not None:
                        response_text = f"{device_name} is online. Response time: {response_time:.2f} ms"
                    else:
                        response_text = f"{device_name} is offline."
                else:
                    response_text = "Device not found in the list."
            else:
                response_text = "Usage: /status <device_name>"
        else:
            # The command has no arguments, so show status for all devices
            response_text = "Device Status:\n"
            for device_name, device_ip in device_list.items():
                response_time = ping_device(device_ip)
                if response_time is not None:
                    response_text += f"{device_name} is online. Response time: {response_time:.2f} ms\n"
                else:
                    response_text += f"{device_name} is offline.\n"

        await event.respond(response_text)
        raise events.StopPropagation

# Call the function to read devices from the devices.txt file
read_devices_from_file('devices.txt')
