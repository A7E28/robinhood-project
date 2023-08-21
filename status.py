import ping3
from telethon import events
import re
import json

def get_response_time(ip):
    try:
        response_time = ping3.ping(ip, timeout=2, unit='ms')
        if response_time is not None:
            return f"{ip}: {response_time:.2f} ms", True
        else:
            return f"{ip}: Offline", False

    except Exception as e:
        print("Ping error:", e)
        return f"{ip}: Host unreachable or invalid IP", False

def get_device_name_and_ip(identifier):
    with open('device.json', 'r') as file:
        data = json.load(file)

    for device in data['devices']:
        if identifier == device['name'] or identifier == device['ip']:
            return device['name'], device['ip']

    return None, None

def save_devices_to_json(devices):
    with open('device.json', 'w') as file:
        json.dump({"devices": devices}, file, indent=4)

def register_status_feature(client):
    @client.on(events.NewMessage(pattern='/status_device'))
    async def check_specific_status(event):
        identifier = event.raw_text.split(maxsplit=1)[1]  # Extract the device name or IP from the message

        device, ip = get_device_name_and_ip(identifier)

        if device is not None and ip is not None:
            response_time, is_online = get_response_time(ip)

            if is_online:
                response_msg = f"{device} is online: {response_time}"
            else:
                response_msg = f"{device} is offline"
        else:
            response_msg = f"Device {identifier} not found in the list."

        await event.respond(response_msg)

    @client.on(events.NewMessage(pattern='/all_status'))
    async def check_all_status(event):
        with open('device.json', 'r') as file:
            data = json.load(file)

        online_msg = "Online Devices:\n"
        offline_msg = ""

        for device in data['devices']:
            name = device['name']
            ip = device['ip']
            response_time, is_online = get_response_time(ip)

            if is_online:
                online_msg += f"{name} ({ip}): {response_time}\n"
            else:
                offline_msg += f"{name} ({ip}): Offline\n"

        response_msg = online_msg
        if offline_msg:
            response_msg += "\nOffline Devices:\n" + offline_msg

        await event.respond(response_msg)

    @client.on(events.NewMessage(pattern=r'/add_device (.+)'))
    async def add_device(event):
        device_info = event.pattern_match.group(1)
        name, ip = re.split(r'\s*,\s*', device_info)

        # Validate IP format
        if not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', ip):
            await event.respond("Invalid IP format. Use: /add_device <name>, <IP>")
            return

        with open('device.json', 'r') as file:
            data = json.load(file)

        data['devices'].append({"name": name, "ip": ip})
        save_devices_to_json(data['devices'])

        await event.respond(f"Device {name} ({ip}) added successfully.")

    @client.on(events.NewMessage(pattern=r'/remove_device (.+)'))
    async def remove_device(event):
        identifier = event.pattern_match.group(1)

        with open('device.json', 'r') as file:
            data = json.load(file)

        new_devices = [device for device in data['devices'] if device['name'] != identifier and device['ip'] != identifier]

        if len(new_devices) < len(data['devices']):
            save_devices_to_json(new_devices)
            await event.respond(f"Device {identifier} removed successfully.")
        else:
            await event.respond(f"Device {identifier} not found in the list.")


    @client.on(events.NewMessage(pattern='/device_list'))
    async def list_devices(event):
        with open('device.json', 'r') as file:
            data = json.load(file)

        device_list_msg = "List of Devices:\n"

        for idx, device in enumerate(data['devices'], start=1):
            name = device['name']
            ip = device['ip']
            device_list_msg += f"{idx}. {name} ({ip})\n"

        await event.respond(device_list_msg)
